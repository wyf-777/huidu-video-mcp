from depth_video_converter.models import detect_device


def test_detect_device_returns_supported_value():
    assert detect_device() in {"cuda", "mps", "cpu"}
