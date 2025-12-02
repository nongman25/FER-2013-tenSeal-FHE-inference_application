"""Session state helpers for Streamlit."""
from __future__ import annotations

import streamlit as st


def init_session_state() -> None:
    defaults = {
        "jwt_token": None,
        "user_id": None,
        "key_id": None,
        "ts_context": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_auth(token: str, user_id: str) -> None:
    st.session_state.jwt_token = token
    st.session_state.user_id = user_id


def set_key_info(key_id: str, ctx) -> None:
    st.session_state.key_id = key_id
    st.session_state.ts_context = ctx
