"""HTTP client for FastAPI backend."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from config import BACKEND_BASE_URL


class APIClient:
    def __init__(self, base_url: str = BACKEND_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None

    # -------------------- Auth --------------------
    def register(self, user_id: str, password: str, email: str | None = None) -> Dict[str, Any]:
        payload = {"user_id": user_id, "password": password, "email": email}
        return self._post("/auth/register", json=payload)

    def login(self, user_id: str, password: str) -> Dict[str, Any]:
        payload = {"user_id": user_id, "password": password}
        res = self._post("/auth/login", json=payload)
        self.token = res.get("access_token")
        return res

    # -------------------- HE key registration --------------------
    def register_he_key(self, key_id: str, eval_context_b64: str) -> Dict[str, Any]:
        payload = {"key_id": key_id, "eval_context_b64": eval_context_b64}
        return self._post("/he/register-key", json=payload)

    # -------------------- Emotion --------------------
    def analyze_today(self, ciphertext_b64: str, key_id: str, target_date: str | None = None) -> Dict[str, Any]:
        payload = {"ciphertext": ciphertext_b64, "key_id": key_id, "date": target_date}
        return self._post("/emotion/analyze-today", json=payload)

    def history_raw(self, days: int, key_id: str) -> Dict[str, Any]:
        params = {"days": days, "key_id": key_id}
        return self._get("/emotion/history-raw", params=params)

    def analyze_history_fhe(self, days: int, key_id: str) -> Dict[str, str]:
        payload = {"days": days, "key_id": key_id}
        return self._post("/emotion/analyze-history", json=payload)

    # -------------------- Internal helpers --------------------
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _post(self, path: str, json: Dict[str, Any] | None = None, timeout: int = 120) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}{path}", json=json or {}, headers=self._headers(), timeout=timeout)
        try:
            res.raise_for_status()
        except requests.HTTPError as exc:
            detail = f"POST {path} -> {res.status_code} {res.reason}; body={res.text}"
            raise requests.HTTPError(detail, response=res) from exc
        return res.json() if res.text else {}

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}{path}", params=params or {}, headers=self._headers(), timeout=30)
        try:
            res.raise_for_status()
        except requests.HTTPError as exc:
            detail = f"GET {path} -> {res.status_code} {res.reason}; body={res.text}"
            raise requests.HTTPError(detail, response=res) from exc
        return res.json() if res.text else {}


def get_client(base_url: str | None = None) -> APIClient:
    return APIClient(base_url=base_url or BACKEND_BASE_URL)
