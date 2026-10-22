"""Command-line interface for automation and non-Gradio testing."""

import argparse
from pathlib import Path

from .constants import MODEL_IDS, RESOLUTION_MAX_SIDE
from .converter import ConversionOptions, DepthVideoConverter, ProgressUpdate
from .errors import ConversionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="将普通视频转换为相对深度图视频")
    parser.add_argument("input", type=Path, help="输入视频路径")
    parser.add_argument("output", type=Path, help="输出MP4路径")
    parser.add_argument("--model", choices=MODEL_IDS, default="small", help="深度模型")
    parser.add_argument(
        "--resolution",
        choices=RESOLUTION_MAX_SIDE,
        default="720p",
        help="输出分辨率",
    )
    parser.add_argument("--invert", action="store_true", help="反转黑白深度")
    parser.add_argument("--keep-audio", action="store_true", help="保留原视频音频")
    parser.add_argument("--no-smoothing", action="store_true", help="关闭时间平滑")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    converter = DepthVideoConverter()
    last_percent = -1

    def report(update: ProgressUpdate) -> None:
        nonlocal last_percent
        percent = int(update.ratio * 100)
        if percent == last_percent or (percent % 5 != 0 and percent != 100):
            return
        last_percent = percent
        print(
            f"\r正在处理：{percent:3d}% "
            f"({update.completed_frames}/{update.total_frames or '?'}) "
            f"[{update.device.upper()}]",
            end="",
            flush=True,
        )

    options = ConversionOptions(
        model_name=arguments.model,
        resolution=arguments.resolution,
        invert=arguments.invert,
        keep_audio=arguments.keep_audio,
        smooth_normalization=not arguments.no_smoothing,
    )
    try:
        result = converter.convert(
            arguments.input,
            options,
            output_path=arguments.output,
            progress_callback=report,
        )
    except ConversionError as exc:
        print(f"\n转换失败：{exc}")
        return 1

    print(f"\n转换完成：{result.output_path}")
    for warning in result.warnings:
        print(f"警告：{warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
