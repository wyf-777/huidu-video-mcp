"""Model loading, caching, and compute-device selection."""

from dataclasses import dataclass
from threading import Lock
from typing import Any

import torch
from transformers import AutoImageProcessor, AutoModelForDepthEstimation

from .constants import MODEL_IDS
from .errors import InvalidOptionsError


def detect_device() -> str:
    """Select CUDA, Apple MPS, or CPU in that order."""
    if torch.cuda.is_available():
        return "cuda"
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"
    return "cpu"


@dataclass(frozen=True, slots=True)
class ModelBundle:
    processor: Any
    model: Any


class ModelRepository:
    """Thread-safe process-local cache; production Workers keep one instance."""

    def __init__(self, device: str | None = None) -> None:
        self.device = device or detect_device()
        self._cache: dict[str, ModelBundle] = {}
        self._lock = Lock()

    def load(self, model_name: str) -> ModelBundle:
        if model_name not in MODEL_IDS:
            raise InvalidOptionsError(f"不支持的模型：{model_name}")

        cached = self._cache.get(model_name)
        if cached is not None:
            return cached

        with self._lock:
            cached = self._cache.get(model_name)
            if cached is not None:
                return cached

            model_id = MODEL_IDS[model_name]
            processor = AutoImageProcessor.from_pretrained(model_id)
            model = AutoModelForDepthEstimation.from_pretrained(model_id).to(self.device)
            model.eval()
            bundle = ModelBundle(processor=processor, model=model)
            self._cache[model_name] = bundle
            return bundle
