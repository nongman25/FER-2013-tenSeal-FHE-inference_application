"""Image preprocessing to match FER2013 pipeline."""
from __future__ import annotations

import io
import numpy as np
import cv2
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


def apply_clahe(gray: np.ndarray, clip: float = 1.5, grid: int = 8) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
    return clahe.apply(gray)


def unsharp(gray: np.ndarray, sigma: float = 0.5, strength: float = 1.5, negative: float = -0.8) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (0, 0), sigma)
    return cv2.addWeighted(gray, strength, blurred, negative, 0)


def clahe_then_unsharp(gray: np.ndarray) -> np.ndarray:
    # CLAHE로 대비 올린 뒤 샤프닝
    clahe_img = apply_clahe(gray, clip=1.8, grid=8)
    return unsharp(clahe_img, sigma=0.4, strength=1.5, negative=-0.6)


def preprocess_image_to_fer2013_format(file_bytes: bytes) -> PreprocessedImage:
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image = image.resize((TARGET_SIZE, TARGET_SIZE))
    grayscale_pil = image.convert("L")

    # Apply CLAHE + unsharp on 48x48 grayscale
    gray_arr = np.array(grayscale_pil).astype(np.uint8)
    processed_arr = clahe_then_unsharp(gray_arr)

    # Keep processed grayscale as PIL image for visualization
    grayscale = Image.fromarray(processed_arr)

    arr = processed_arr.astype(np.float32) / 255.0
    normalized = (arr - NORMALIZATION_MEAN) / max(NORMALIZATION_STD, 1e-6)
    vector = normalized.flatten()
    return PreprocessedImage(vector=vector, original=image, grayscale=grayscale)
