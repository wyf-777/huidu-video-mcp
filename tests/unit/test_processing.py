import numpy as np
import pytest

from depth_video_converter.processing import (
    TemporalBounds,
    calculate_output_size,
    normalize_depth,
)


@pytest.mark.parametrize(
    ("width", "height", "max_side", "expected"),
    [
        (1920, 1080, None, (1920, 1080)),
        (1920, 1080, 1280, (1280, 720)),
        (1080, 1920, 640, (360, 640)),
        (641, 359, 640, (640, 358)),
        (320, 240, 1280, (320, 240)),
    ],
)
def test_calculate_output_size(width, height, max_side, expected):
    assert calculate_output_size(width, height, max_side) == expected


@pytest.mark.parametrize(("width", "height"), [(0, 10), (10, 0), (-1, 10)])
def test_calculate_output_size_rejects_invalid_source(width, height):
    with pytest.raises(ValueError):
        calculate_output_size(width, height, 640)


def test_normalize_depth_maps_bounds_to_grayscale():
    depth = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)

    result = normalize_depth(depth, 0.0, 1.0, invert=False)

    np.testing.assert_array_equal(result, np.array([[0, 127, 255]], dtype=np.uint8))


def test_normalize_depth_can_invert_and_handle_non_finite_values():
    depth = np.array([[np.nan, np.inf, -np.inf]], dtype=np.float32)

    result = normalize_depth(depth, 0.0, 1.0, invert=True)

    np.testing.assert_array_equal(result, np.array([[255, 0, 255]], dtype=np.uint8))


def test_temporal_bounds_uses_exponential_moving_average():
    bounds = TemporalBounds(alpha=0.25)

    assert bounds.update(0.0, 10.0) == (0.0, 10.0)
    assert bounds.update(4.0, 14.0) == (1.0, 11.0)


def test_temporal_bounds_rejects_invalid_alpha():
    with pytest.raises(ValueError):
        TemporalBounds(alpha=0.0)
