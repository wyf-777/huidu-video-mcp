"""Video finalization helpers isolated from model inference."""

import shutil
import subprocess
from pathlib import Path


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def finalize_video(
    silent_video: Path,
    source_video: Path,
    output_video: Path,
    *,
    keep_audio: bool,
) -> tuple[str, ...]:
    """Create the final output and return non-fatal warnings."""
    output_video.parent.mkdir(parents=True, exist_ok=True)

    if not ffmpeg_available():
        shutil.copy2(silent_video, output_video)
        warning = "未检测到FFmpeg，输出使用mp4v编码且不保留音频"
        return (warning,)

    command = ["ffmpeg", "-y", "-i", str(silent_video)]
    if keep_audio:
        command.extend(["-i", str(source_video), "-map", "0:v:0", "-map", "1:a:0?"])
    command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"])
    if keep_audio:
        command.extend(["-c:a", "aac", "-shortest"])
    command.append(str(output_video))

    try:
        subprocess.run(command, check=True, capture_output=True, timeout=None)
    except (OSError, subprocess.CalledProcessError):
        shutil.copy2(silent_video, output_video)
        return ("FFmpeg转码失败，已返回无音频的mp4v兼容输出",)
    return ()
