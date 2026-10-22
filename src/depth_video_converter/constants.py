"""Stable model and resolution identifiers shared by every entry point."""

MODEL_IDS: dict[str, str] = {
    "small": "depth-anything/Depth-Anything-V2-Small-hf",
    "base": "depth-anything/Depth-Anything-V2-Base-hf",
    "large": "depth-anything/Depth-Anything-V2-Large-hf",
}

MODEL_LABELS: dict[str, str] = {
    "Small（高速，推荐）": "small",
    "Base（平衡）": "base",
    "Large（高质量，较慢）": "large",
}

RESOLUTION_MAX_SIDE: dict[str, int | None] = {
    "source": None,
    "1080p": 1920,
    "720p": 1280,
    "540p": 960,
    "480p": 854,
    "360p": 640,
}

RESOLUTION_LABELS: dict[str, str] = {
    "保持原始分辨率": "source",
    "1080p（长边1920）": "1080p",
    "720p（长边1280）": "720p",
    "540p（长边960）": "540p",
    "480p（长边854）": "480p",
    "360p（长边640，最快）": "360p",
}

DEFAULT_MODEL = "small"
DEFAULT_RESOLUTION = "720p"
