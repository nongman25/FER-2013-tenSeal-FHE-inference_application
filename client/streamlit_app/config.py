"""Configuration for the Streamlit FHE client."""
from __future__ import annotations

import os

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
KEY_DIR = os.getenv("FHE_KEY_DIR", "keys")
