"""Image preprocessing to match FER2013 pipeline."""
from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image

# TODO: keep in sync with backend normalization_stats.json
NORMALIZATION_MEAN = 0.507
NORMALIZATION_STD = 0.255
TARGET_SIZE = 48


class PreprocessedImage:
    def __init__(self, vector: np.ndarray, original: Image.Image, grayscale: Image.Image) -> None:
        self.vector = vector.astype(np.float32)
        self.original = original
        self.grayscale = grayscale


def preprocess_image_to_fer2013_format(file_bytes: bytes) -> PreprocessedImage:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image = image.resize((TARGET_SIZE, TARGET_SIZE))
    grayscale = image.convert("L")

    arr = np.array(grayscale).astype(np.float32) / 255.0
    normalized = (arr - NORMALIZATION_MEAN) / max(NORMALIZATION_STD, 1e-6)
    vector = normalized.flatten()
    return PreprocessedImage(vector=vector, original=image, grayscale=grayscale)
