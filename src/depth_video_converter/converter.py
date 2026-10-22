"""Framework-independent depth-video conversion service."""

import math
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from .constants import DEFAULT_MODEL, DEFAULT_RESOLUTION, MODEL_IDS, RESOLUTION_MAX_SIDE
from .errors import InputVideoError, InvalidOptionsError, OutputVideoError
from .media import finalize_video
from .models import ModelRepository
from .processing import TemporalBounds, calculate_output_size, normalize_depth


@dataclass(frozen=True, slots=True)
class ConversionOptions:
    model_name: str = DEFAULT_MODEL
    resolution: str = DEFAULT_RESOLUTION
    invert: bool = False
    keep_audio: bool = False
    smooth_normalization: bool = True


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    completed_frames: int
    total_frames: int
    stage: str
    device: str

    @property
    def ratio(self) -> float:
        if self.total_frames <= 0:
            return 0.0
        return min(1.0, self.completed_frames / self.total_frames)


@dataclass(frozen=True, slots=True)
class ConversionResult:
    output_path: Path
    processed_frames: int
    fps: float
    width: int
    height: int
    device: str
    warnings: tuple[str, ...] = ()


ProgressCallback = Callable[[ProgressUpdate], None]


class DepthVideoConverter:
    """Convert one input video using an injected process-local model repository."""

    def __init__(self, models: ModelRepository | None = None) -> None:
        self.models = models or ModelRepository()

    def convert(
        self,
        input_path: str | Path,
        options: ConversionOptions,
        *,
        output_path: str | Path | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> ConversionResult:
        source = Path(input_path)
        if not source.is_file():
            raise InputVideoError("输入视频不存在或无法访问")
        self._validate_options(options)

        if output_path is None:
            work_dir = Path(tempfile.mkdtemp(prefix="depth_video_"))
            destination = work_dir / "depth_output.mp4"
            try:
                return self._convert_in_directory(
                    source, destination, work_dir, options, progress_callback
                )
            except Exception:
                shutil.rmtree(work_dir, ignore_errors=True)
                raise

        destination = Path(output_path)
        if source.resolve() == destination.resolve():
            raise InvalidOptionsError("输出路径不能覆盖输入视频")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="depth_video_") as temporary:
            return self._convert_in_directory(
                source, destination, Path(temporary), options, progress_callback
            )

    def _convert_in_directory(
        self,
        source: Path,
        destination: Path,
        work_dir: Path,
        options: ConversionOptions,
        progress_callback: ProgressCallback | None,
    ) -> ConversionResult:
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise InputVideoError("无法读取视频，请检查文件格式")

        try:
            fps, total_frames, output_width, output_height = self._inspect_video(
                capture, options.resolution
            )
            bundle = self.models.load(options.model_name)
            silent_path = work_dir / "depth_silent.mp4"
            processed_frames = self._process_frames(
                capture=capture,
                silent_path=silent_path,
                fps=fps,
                total_frames=total_frames,
                output_width=output_width,
                output_height=output_height,
                processor=bundle.processor,
                model=bundle.model,
                options=options,
                progress_callback=progress_callback,
            )
        finally:
            capture.release()

        if processed_frames == 0:
            raise InputVideoError("视频中没有可读取的画面")

        warnings = finalize_video(
            silent_path,
            source,
            destination,
            keep_audio=options.keep_audio,
        )
        if not destination.is_file() or destination.stat().st_size == 0:
            raise OutputVideoError("输出视频写入失败")

        return ConversionResult(
            output_path=destination,
            processed_frames=processed_frames,
            fps=fps,
            width=output_width,
            height=output_height,
            device=self.models.device,
            warnings=warnings,
        )

    def _inspect_video(
        self, capture: cv2.VideoCapture, resolution: str
    ) -> tuple[float, int, int, int]:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not math.isfinite(fps) or fps <= 0:
            fps = 30.0
        total_frames = max(0, int(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        try:
            output_width, output_height = calculate_output_size(
                source_width,
                source_height,
                RESOLUTION_MAX_SIDE[resolution],
            )
        except ValueError as exc:
            raise InputVideoError("无法读取有效的视频尺寸") from exc
        return fps, total_frames, output_width, output_height

    def _process_frames(
        self,
        *,
        capture: cv2.VideoCapture,
        silent_path: Path,
        fps: float,
        total_frames: int,
        output_width: int,
        output_height: int,
        processor: object,
        model: object,
        options: ConversionOptions,
        progress_callback: ProgressCallback | None,
    ) -> int:
        writer = cv2.VideoWriter(
            str(silent_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (output_width, output_height),
        )
        if not writer.isOpened():
            raise OutputVideoError("无法创建输出视频文件")

        temporal_bounds = TemporalBounds() if options.smooth_normalization else None
        processed_frames = 0
        try:
            with torch.inference_mode():
                while True:
                    success, frame = capture.read()
                    if not success:
                        break

                    depth = self._estimate_depth(
                        frame, processor, model, output_width, output_height
                    )
                    finite_depth = depth[np.isfinite(depth)]
                    if finite_depth.size == 0:
                        raise OutputVideoError("模型返回了无效的深度结果")
                    current_minimum = float(finite_depth.min())
                    current_maximum = float(finite_depth.max())
                    if temporal_bounds is None:
                        lower_bound, upper_bound = current_minimum, current_maximum
                    else:
                        lower_bound, upper_bound = temporal_bounds.update(
                            current_minimum, current_maximum
                        )

                    grayscale = normalize_depth(
                        depth,
                        lower_bound,
                        upper_bound,
                        invert=options.invert,
                    )
                    writer.write(cv2.cvtColor(grayscale, cv2.COLOR_GRAY2BGR))
                    processed_frames += 1
                    if progress_callback is not None:
                        progress_callback(
                            ProgressUpdate(
                                completed_frames=processed_frames,
                                total_frames=total_frames,
                                stage="inference",
                                device=self.models.device,
                            )
                        )
        finally:
            writer.release()
        return processed_frames

    def _estimate_depth(
        self,
        frame: np.ndarray,
        processor: object,
        model: object,
        output_width: int,
        output_height: int,
    ) -> np.ndarray:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        inputs = processor(images=Image.fromarray(rgb_frame), return_tensors="pt").to(
            self.models.device
        )
        outputs = model(**inputs)
        resized_depth = torch.nn.functional.interpolate(
            outputs.predicted_depth.unsqueeze(1),
            size=(output_height, output_width),
            mode="bicubic",
            align_corners=False,
        )
        return resized_depth.squeeze().float().cpu().numpy()

    @staticmethod
    def _validate_options(options: ConversionOptions) -> None:
        if options.model_name not in MODEL_IDS:
            raise InvalidOptionsError(f"不支持的模型：{options.model_name}")
        if options.resolution not in RESOLUTION_MAX_SIDE:
            raise InvalidOptionsError(f"不支持的输出分辨率：{options.resolution}")
