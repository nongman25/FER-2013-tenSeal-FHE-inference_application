"""Key generation/loading utilities for TenSEAL CKKS."""
from __future__ import annotations

import base64
import json
import uuid
from hashlib import sha256
from pathlib import Path
from typing import Tuple

import tenseal as ts

from config import KEY_DIR

KEY_DIR_PATH = Path(KEY_DIR)
KEYPAIR_PATH = KEY_DIR_PATH / "fhe-emotion-keypair.seal"
EVAL_STATE_PATH = KEY_DIR_PATH / "fhe-eval-context.seal"
META_PATH = KEY_DIR_PATH / "key_meta.json"

# Match backend defaults (see he/tenseal_context.py)
DEFAULT_POLY_MODULUS_DEGREE = 32768
DEFAULT_COEFF_MOD_BIT_SIZES = (60, 40, 40, 40, 40, 40, 40, 40, 60)
DEFAULT_GLOBAL_SCALE = 2**40



def _ensure_dir() -> None:
    KEY_DIR_PATH.mkdir(parents=True, exist_ok=True)


def keypair_exists() -> bool:
    return KEYPAIR_PATH.exists() and META_PATH.exists()


def load_client_context() -> ts.Context:
    data = KEYPAIR_PATH.read_bytes()
    return ts.context_from(data)


def _compute_key_id(eval_bytes: bytes) -> str:
    return sha256(eval_bytes).hexdigest()[:16]


def generate_and_store_keys() -> Tuple[ts.Context, str, str]:
    """Generate CKKS context, save client+eval contexts, and return eval b64 for registration."""
    _ensure_dir()
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=DEFAULT_POLY_MODULUS_DEGREE,
        coeff_mod_bit_sizes=list(DEFAULT_COEFF_MOD_BIT_SIZES),
    )
    context.global_scale = DEFAULT_GLOBAL_SCALE
    context.generate_galois_keys()
    context.generate_relin_keys()

    client_bytes = context.serialize(save_secret_key=True, save_public_key=True, save_galois_keys=True, save_relin_keys=True)
    eval_bytes = context.serialize(save_secret_key=False, save_public_key=True, save_galois_keys=True, save_relin_keys=True)

    key_id = str(uuid.uuid4())
    KEYPAIR_PATH.write_bytes(client_bytes)
    EVAL_STATE_PATH.write_bytes(eval_bytes)
    META_PATH.write_text(json.dumps({"key_id": key_id}))

    eval_context_b64 = base64.b64encode(eval_bytes).decode("utf-8")
    return context, key_id, eval_context_b64


def ensure_client_context() -> Tuple[ts.Context, str, str | None]:
    """Load existing context or generate a new one.

    Returns (context, key_id, eval_context_b64_if_new)
    eval_context_b64 is returned even for existing keys to allow re-registration.
    """
    if keypair_exists():
        ctx = load_client_context()
        eval_bytes = EVAL_STATE_PATH.read_bytes() if EVAL_STATE_PATH.exists() else b""
        meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
        key_id = meta.get("key_id") or _compute_key_id(eval_bytes)
        # Always return eval context to allow re-registration
        if not eval_bytes:
            eval_bytes = ctx.serialize(save_secret_key=False, save_public_key=True, save_galois_keys=True, save_relin_keys=True)
            EVAL_STATE_PATH.write_bytes(eval_bytes)
        eval_context_b64 = base64.b64encode(eval_bytes).decode("utf-8")
        return ctx, key_id, eval_context_b64

    # No existing keypair: generate
    return generate_and_store_keys()


def get_eval_context_b64() -> str:
    """Return base64 of evaluation context (no secret key)."""
    if EVAL_STATE_PATH.exists():
        return base64.b64encode(EVAL_STATE_PATH.read_bytes()).decode("utf-8")
    _, _, eval_b64 = generate_and_store_keys()
    return eval_b64
