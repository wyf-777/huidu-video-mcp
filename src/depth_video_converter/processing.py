"""Pure image-processing functions used by the converter and its tests."""

from dataclasses import dataclass

import numpy as np


def calculate_output_size(width: int, height: int, max_side: int | None) -> tuple[int, int]:
    """Scale down to ``max_side`` without upscaling and return even dimensions."""
    if width <= 0 or height <= 0:
        raise ValueError("视频宽高必须大于0")
    if max_side is not None and max_side < 2:
        raise ValueError("最长边必须大于或等于2")

    scale = 1.0 if max_side is None else min(1.0, max_side / max(width, height))
    output_width = max(2, int(width * scale) // 2 * 2)
    output_height = max(2, int(height * scale) // 2 * 2)
    return output_width, output_height


def normalize_depth(
    depth: np.ndarray,
    lower_bound: float,
    upper_bound: float,
    *,
    invert: bool,
) -> np.ndarray:
    """Convert a depth array into an 8-bit grayscale frame."""
    safe_depth = np.nan_to_num(
        depth.astype(np.float32, copy=False),
        nan=lower_bound,
        posinf=upper_bound,
        neginf=lower_bound,
    )
    normalized = np.clip(
        (safe_depth - lower_bound) / max(upper_bound - lower_bound, 1e-6),
        0.0,
        1.0,
    )
    if invert:
        normalized = 1.0 - normalized
    return (normalized * 255).astype(np.uint8)


@dataclass(slots=True)
class TemporalBounds:
    """Exponential moving bounds used to reduce frame-to-frame flicker."""

    alpha: float = 0.05
    minimum: float | None = None
    maximum: float | None = None

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise ValueError("alpha必须位于(0, 1]区间")

    def update(self, current_minimum: float, current_maximum: float) -> tuple[float, float]:
        if self.minimum is None or self.maximum is None:
            self.minimum = current_minimum
            self.maximum = current_maximum
        else:
            self.minimum = (1.0 - self.alpha) * self.minimum + self.alpha * current_minimum
            self.maximum = (1.0 - self.alpha) * self.maximum + self.alpha * current_maximum
        return self.minimum, self.maximum
