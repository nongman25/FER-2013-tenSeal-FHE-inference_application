"""Adapter over the existing TenSEAL/FHE inference utilities.

This module centralizes interaction with TenSEAL and the FHE-friendly CNN.
If TenSEAL or model assets are unavailable in the prototype environment, it
falls back to a stub encoder/decoder that preserves the ciphertext interface
while running plain inference for developer feedback.
"""
from __future__ import annotations

import base64
import json
import logging
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from app.core.config import settings

LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@dataclass
class StubPrediction:
    label: str
    probabilities: list[float] | None
    raw: dict[str, Any]


class HEEmotionEngine:
    """High-level HE emotion engine entry point.

    The class tries to initialize the real TenSEAL pipeline using the existing
    `he/` and `models/` modules in the parent project. If that fails (e.g.,
    TenSEAL not installed), it switches to a stub that still respects the
    ciphertext interface by base64-encoding JSON payloads.
    """

    def __init__(self) -> None:
        self._project_root = self._bootstrap_project_root()
        self._runner = None
        self._context = None
        self._plain_model = None
        self._norm_stats = None
        self._torch = None
        self._use_stub = False
        self.class_labels = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

        self._initialize_engine()

    def _bootstrap_project_root(self) -> Path:
        try:
            root = Path(__file__).resolve().parents[4]
        except IndexError:
            root = Path(__file__).resolve().parent
        if str(root) not in sys.path:
            sys.path.append(str(root))
        return root

    def _initialize_engine(self) -> None:
        """Attempt to wire up TenSEAL; otherwise fall back to stub mode."""
        try:
            import torch
            from he.tenseal_context import create_context
            from he.fhe_inference import PackedEncryptedCNNRunner, load_plain_model
            from models.fhe_cnn import extract_fhe_parameters

            self._torch = torch
            self._context = create_context()
            model, stats = load_plain_model(device=torch.device("cpu"))
            params = extract_fhe_parameters(model)
            self._runner = PackedEncryptedCNNRunner(self._context, params, log_steps=False)
            self._plain_model = model
            self._norm_stats = stats
            LOGGER.info("HE engine initialized with TenSEAL context")
        except Exception as exc:  # noqa: BLE001 - fallback stub is intended
            LOGGER.warning("Falling back to stub HE engine: %s", exc)
            self._use_stub = True
            self._prepare_stub_model()

    def _prepare_stub_model(self) -> None:
        try:
            import torch
            from he.fhe_inference import load_plain_model

            self._torch = torch
            self._plain_model, self._norm_stats = load_plain_model(device=torch.device("cpu"))
        except Exception as exc:  # noqa: BLE001 - optional path
            LOGGER.warning("Plain model unavailable for stub inference: %s", exc)
            self._plain_model = None
            self._norm_stats = None

    # --- Serialization helpers (stub) ---
    def _encode_stub_ciphertext(self, payload: dict[str, Any]) -> str:
        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        return encoded

    def _decode_stub_ciphertext(self, payload: str) -> dict[str, Any] | None:
        try:
            decoded_bytes = base64.b64decode(payload.encode("utf-8"))
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception:  # noqa: BLE001 - keep ciphertext opaque if decode fails
            return None

    # --- Core API ---
    def run_encrypted_inference(self, enc_image_payload: str, key_id: str) -> str:
        """Run encrypted inference.

        In stub mode, the ciphertext is treated as base64(JSON) containing a
        flattened 48x48 image under the ``data`` key. The output is an encoded
        JSON with predicted label and probabilities.
        """
        if not self._use_stub and self._runner is not None:
            # TODO: implement TenSEAL deserialization when client encryption is wired.
            LOGGER.debug("TenSEAL path not wired; using stub serialization")
        prediction = self._stub_inference(enc_image_payload, key_id)
        return prediction

    def _stub_inference(self, enc_image_payload: str, key_id: str) -> str:
        decoded = self._decode_stub_ciphertext(enc_image_payload) or {}
        data: Iterable[float] | None = None
        if isinstance(decoded, dict):
            data = decoded.get("data") or decoded.get("vector")
        stub_prediction = self._run_plain_model(data)
        response = {
            "key_id": key_id,
            "prediction": stub_prediction.label,
            "probabilities": stub_prediction.probabilities,
            "opaque": True,
            "meta": {"note": "stub ciphertext", "echo": decoded},
        }
        return self._encode_stub_ciphertext(response)

    def _run_plain_model(self, data: Iterable[float] | None) -> StubPrediction:
        if self._plain_model is None or self._torch is None or data is None:
            return StubPrediction(label="unknown", probabilities=None, raw={})

        try:
            arr = list(data)
            if len(arr) != 48 * 48:
                raise ValueError("Expected 2304 values for 48x48 image")
            tensor = self._torch.tensor(arr, dtype=self._torch.float32).view(1, 48, 48)
            if self._norm_stats:
                tensor = self._norm_stats.normalize(tensor)
            input_tensor = tensor.unsqueeze(0)
            with self._torch.no_grad():
                logits = self._plain_model(input_tensor).squeeze(0)
                probs = self._torch.softmax(logits, dim=-1)
            pred_idx = int(self._torch.argmax(probs).item())
            label = self.class_labels[pred_idx] if pred_idx < len(self.class_labels) else str(pred_idx)
            probabilities = [float(p) for p in probs.tolist()]
            return StubPrediction(label=label, probabilities=probabilities, raw={})
        except Exception as exc:  # noqa: BLE001 - keep stub resilient
            LOGGER.warning("Stub model inference failed: %s", exc)
            return StubPrediction(label="unknown", probabilities=None, raw={})

    def postprocess_prediction_to_summary(self, enc_logits_payload: str, target_date: date) -> str:
        """Optionally transform logits to a daily summary ciphertext."""
        decoded = self._decode_stub_ciphertext(enc_logits_payload) or {"ciphertext": enc_logits_payload}
        summary = {
            "date": target_date.isoformat(),
            "payload": decoded,
            "note": "summary stub",
        }
        return self._encode_stub_ciphertext(summary)
