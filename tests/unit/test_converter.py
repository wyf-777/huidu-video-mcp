from pathlib import Path

import pytest

from depth_video_converter.converter import ConversionOptions, DepthVideoConverter, ProgressUpdate
from depth_video_converter.errors import InputVideoError, InvalidOptionsError


def test_progress_ratio_handles_unknown_total():
    update = ProgressUpdate(4, 0, "inference", "cpu")

    assert update.ratio == 0.0


def test_progress_ratio_is_capped_at_one():
    update = ProgressUpdate(11, 10, "inference", "cpu")

    assert update.ratio == 1.0


def test_converter_rejects_missing_input(tmp_path: Path):
    converter = DepthVideoConverter()

    with pytest.raises(InputVideoError):
        converter.convert(tmp_path / "missing.mp4", ConversionOptions())


def test_converter_rejects_unknown_resolution(tmp_path: Path):
    source = tmp_path / "video.mp4"
    source.touch()
    converter = DepthVideoConverter()

    with pytest.raises(InvalidOptionsError):
        converter.convert(source, ConversionOptions(resolution="invalid"))


def test_converter_rejects_unknown_model(tmp_path: Path):
    source = tmp_path / "video.mp4"
    source.touch()
    converter = DepthVideoConverter()

    with pytest.raises(InvalidOptionsError):
        converter.convert(source, ConversionOptions(model_name="invalid"))


def test_converter_does_not_overwrite_input(tmp_path: Path):
    source = tmp_path / "video.mp4"
    source.touch()
    converter = DepthVideoConverter()

    with pytest.raises(InvalidOptionsError):
        converter.convert(source, ConversionOptions(), output_path=source)
