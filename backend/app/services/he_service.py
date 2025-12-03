"""Adapter over the existing TenSEAL/FHE inference utilities (no stubs).

This version enforces true end-to-end FHE:
- Clients own the secret key and send only evaluation contexts + ciphertexts.
- The server loads evaluation-only contexts per key_id and performs encrypted CNN ops.
- Stub/fallback paths are removed; TenSEAL and model weights must be available.
"""
from __future__ import annotations

import base64
import logging
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings

LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class HEEmotionEngine:
    """High-level HE emotion engine entry point."""

    def __init__(self) -> None:
        self._project_root = self._bootstrap_project_root()
        self._context_dir = self._project_root / "he" / "contexts"
        self._context_dir.mkdir(parents=True, exist_ok=True)
        self._contexts: dict[str, Any] = {}

        self._runner_weights: Optional[Dict[str, Any]] = None
        self._torch = None
        self._ts = None
        self.class_labels = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]

        self._initialize_engine()

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------
    def _bootstrap_project_root(self) -> Path:
        try:
            root = Path(__file__).resolve().parents[4]
        except IndexError:
            root = Path(__file__).resolve().parent
        if str(root) not in sys.path:
            sys.path.append(str(root))
        return root

    def _initialize_engine(self) -> None:
        try:
            import torch
            import tenseal as ts
            from app.fhe_core import fhe_inference
            from app.fhe_core.fhe_cnn import extract_fhe_parameters

            self._torch = torch
            self._ts = ts

            # Override model path to use local copy under backend/app/inference_model
            local_model_path = self._project_root / "backend" / "app" / "inference_model" / "he_cnn_fer2013_enhanced.pt"
            if local_model_path.exists():
                fhe_inference.MODEL_PATH = local_model_path

            model, _ = fhe_inference.load_plain_model(device=torch.device("cpu"))
            params = extract_fhe_parameters(model)
            # Precompute weights in Python lists for encrypted ops
            self._runner_weights = {
                "conv1_weight": params["conv"][0]["weight"].tolist(),
                "conv1_bias": params["conv"][0]["bias"].tolist(),
                "fc1_weight": params["linear"][0]["weight"].T.tolist(),
                "fc1_bias": params["linear"][0]["bias"].tolist(),
                "fc2_weight": params["linear"][1]["weight"].T.tolist(),
                "fc2_bias": params["linear"][1]["bias"].tolist(),
            }
            LOGGER.info("HE engine initialized with TenSEAL and model weights")
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to initialize HE engine: {exc}") from exc

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------
    def register_eval_context(self, key_id: str, eval_context_b64: str) -> None:
        """Register a new evaluation context (no secret key) for a client."""
        data = base64.b64decode(eval_context_b64.encode("utf-8"))
        path = self._context_dir / f"{key_id}.seal"
        path.write_bytes(data)
        if self._ts:
            try:
                ctx = self._ts.context_from(data)
                # Safety: warn if secret key is present
                if hasattr(ctx, "is_public") and not ctx.is_public():
                    LOGGER.warning("Received context for %s contains a secret key; server should not have it", key_id)
                self._contexts[key_id] = ctx
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Unable to load TenSEAL context for %s: %s", key_id, exc)
        LOGGER.info("Registered eval context for key_id=%s at %s", key_id, path)

    def _load_context_from_disk(self, key_id: str):
        if key_id in self._contexts:
            return self._contexts[key_id]
        path = self._context_dir / f"{key_id}.seal"
        if not path.exists():
            raise ValueError(f"No eval context found for key_id={key_id}")
        data = path.read_bytes()
        if not self._ts:
            raise RuntimeError("TenSEAL not available in this environment")
        ctx = self._ts.context_from(data)
        self._contexts[key_id] = ctx
        LOGGER.info("🔑 Loaded eval context for key_id=%s from %s", key_id, path)
        return ctx

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def run_encrypted_inference(self, enc_image_payload: str, key_id: str) -> str:
        """Run encrypted inference. Input/output are base64-encoded serialized CKKS vectors."""
        start = time.perf_counter()
        if not self._ts or not self._runner_weights:
            raise RuntimeError("HE engine not fully initialized (TenSEAL/weights missing)")

        ctx = self._load_context_from_disk(key_id)
        ciphertext_bytes = base64.b64decode(enc_image_payload.encode("utf-8"))
        enc_x = self._ts.ckks_vector_from(ctx, ciphertext_bytes)
        enc_logits = self._forward_im2col(enc_x)
        logits_bytes = enc_logits.serialize()
        elapsed = (time.perf_counter() - start) * 1000
        LOGGER.info("🤖 Encrypted CNN inference done for key_id=%s (%.1f ms)", key_id, elapsed)
        return base64.b64encode(logits_bytes).decode("utf-8")

    def _forward_im2col(self, enc_x):
        """Encrypted CNN forward pass starting from im2col-encoded ciphertext."""
        ts = self._ts
        w = self._runner_weights
        windows_nb = 49  # for 48x48 input, kernel 9, stride 6

        # Conv1
        enc_channels = []
        for kernel, bias in zip(w["conv1_weight"], w["conv1_bias"]):
            k_flat = kernel[0]  # in_channel = 1
            y = enc_x.conv2d_im2col(k_flat, windows_nb) + bias
            enc_channels.append(y)

        # Pack channels
        enc_x = ts.CKKSVector.pack_vectors(enc_channels)
        enc_x.square_()

        # FC1
        enc_x = enc_x.mm(w["fc1_weight"]) + w["fc1_bias"]
        enc_x.square_()

        # FC2
        enc_x = enc_x.mm(w["fc2_weight"]) + w["fc2_bias"]
        return enc_x

    def postprocess_prediction_to_summary(self, enc_logits_payload: str, target_date: date) -> str:
        """Optional hook: for now return logits as-is."""
        return enc_logits_payload
