"""Streamlit client for end-to-end FHE emotion recognition."""
from __future__ import annotations

import base64
from typing import List

import numpy as np
import streamlit as st
import tenseal as ts

import datetime

from diagnostics import MentalHealthDiagnostics

from api_client import get_client
from fhe_keys import ensure_client_context
from preprocessing import preprocess_image_to_fer2013_format
from state import init_session_state, set_auth, set_key_info

EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
KERNEL_SIZE = 9
STRIDE = 6
WINDOWS_NB = 49  # 7x7 windows for 48x48 input


def softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x)


def encrypt_image(ctx: ts.Context, vector: np.ndarray) -> str:
    """Encrypt preprocessed 48x48 image using im2col encoding."""
    image_list = vector.reshape(48, 48).tolist()
    enc_x, _ = ts.im2col_encoding(ctx, image_list, KERNEL_SIZE, KERNEL_SIZE, STRIDE)
    return base64.b64encode(enc_x.serialize()).decode("utf-8")


def decrypt_logits(ctx: ts.Context, logits_b64: str) -> np.ndarray:
    logits_bytes = base64.b64decode(logits_b64.encode("utf-8"))
    enc_logits = ts.ckks_vector_from(ctx, logits_bytes)
    logits = np.array(enc_logits.decrypt())
    # FC2 outputs 7 classes
    return logits[: len(EMOTION_LABELS)]


def render_auth(client):
    st.header("Auth")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Register")
        with st.form("register_form"):
            reg_user = st.text_input("User ID", key="reg_user")
            reg_email = st.text_input("Email", key="reg_email")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            submitted = st.form_submit_button("Register")
            if submitted:
                try:
                    res = client.register(reg_user, reg_pass, reg_email or None)
                    st.success(f"Registered: {res}")
                except Exception as e:
                    st.error(f"Register failed: {e}")

    with col2:
        st.subheader("Login")
        with st.form("login_form"):
            login_user = st.text_input("User ID", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login")
            if submitted:
                try:
                    res = client.login(login_user, login_pass)
                    set_auth(res.get("access_token"), login_user)
                    st.success("Logged in")
                except Exception as e:
                    st.error(f"Login failed: {e}")


def render_key_setup(client):
    st.header("Key setup")
    if not st.session_state.jwt_token:
        st.info("Login first to register keys with the backend.")
        return

    client.token = st.session_state.jwt_token
    if st.button("Ensure local keypair & register eval context"):
        ctx, key_id, eval_b64 = ensure_client_context()
        if eval_b64:
            try:
                client.register_he_key(key_id, eval_b64)
                st.success(f"✅ Registered eval context for key_id={key_id}")
            except Exception as e:
                st.error(f"❌ Registration failed: {str(e)}")
        else:
            st.warning("⚠️ No eval context to register (this shouldn't happen)")
        set_key_info(key_id, ctx)

    if st.session_state.key_id:
        st.write(f"Active key_id: {st.session_state.key_id}")
    else:
        st.warning("No key registered yet. Click the button above.")


def render_today(client):
    st.header("Today’s emotion (E2E FHE)")
    if not st.session_state.jwt_token:
        st.info("Login first.")
        return
    if not st.session_state.ts_context or not st.session_state.key_id:
        st.info("Register/load your keys first.")
        return

    client.token = st.session_state.jwt_token
    target_date = st.date_input("Select target date", value=datetime.date.today())
    uploaded = st.file_uploader("Upload face image", type=["jpg", "jpeg", "png"]) 
    if uploaded:
        prep = preprocess_image_to_fer2013_format(uploaded.read())
        st.image([prep.original, prep.grayscale], caption=["Original", "Grayscale 48x48"], width=240)

        if st.button("Encrypt and analyze today"):
            ciphertext_b64 = encrypt_image(st.session_state.ts_context, prep.vector)
            resp = client.analyze_today(ciphertext_b64, st.session_state.key_id, target_date.isoformat())
            logits = decrypt_logits(st.session_state.ts_context, resp["ciphertext"])
            probs = softmax(logits)
            label_idx = int(np.argmax(probs))
            label = EMOTION_LABELS[label_idx]

            st.success(f"Prediction for {resp.get('date')}: {label}")
            chart_data = {"label": EMOTION_LABELS, "prob": probs}
            st.bar_chart(chart_data, x="label", y="prob")


def render_history(client):
    st.header("N-day history (client-side decrypt)")
    if not st.session_state.jwt_token:
        st.info("Login first.")
        return
    if not st.session_state.ts_context or not st.session_state.key_id:
        st.info("Register/load your keys first.")
        return

    client.token = st.session_state.jwt_token
    days = st.slider("Days", min_value=1, max_value=30, value=7)
    if st.button("Fetch history"):
        resp = client.history_raw(days, st.session_state.key_id)
        entries = resp.get("entries", [])
        if not entries:
            st.info("No history yet.")
            return

        rows: List[dict] = []
        freq = {label: 0 for label in EMOTION_LABELS}
        for item in entries:
            logits = decrypt_logits(st.session_state.ts_context, item["ciphertext"])
            probs = softmax(logits)
            label_idx = int(np.argmax(probs))
            label = EMOTION_LABELS[label_idx]
            freq[label] += 1
            rows.append({"date": item["date"], "label": label, "max_prob": float(probs[label_idx])})

        st.table(rows)
        freq_rows = [{"label": k, "count": v} for k, v in freq.items() if v > 0]
        if freq_rows:
            st.bar_chart(freq_rows, x="label", y="count")
    if st.button("Run Server-Side FHE Analysis"):
        ctx = st.session_state.ts_context
        with st.spinner("Requesting Homomorphic Aggregation to Server..."):
            try:
                resp = client.analyze_history_fhe(days, st.session_state.key_id)
                
                enc_sum_b64 = resp["encrypted_sum"]
                enc_vol_b64 = resp["encrypted_volatility"]
                
                st.success("Received encrypted statistics from server!")
                
            except Exception as e:
                st.error(f"Server Error: {e}")
                st.warning("데이터가 부족하거나 서버 설정이 잘못되었을 수 있습니다.")
                return

        with st.spinner("Decrypting & Diagnosing..."):
            try:
                # Base64 -> CKKSVector -> Decrypt
                enc_sum = ts.ckks_vector_from(ctx, base64.b64decode(enc_sum_b64))
                enc_vol = ts.ckks_vector_from(ctx, base64.b64decode(enc_vol_b64))
                
                plain_sum = np.array(enc_sum.decrypt())[:7]
                plain_vol = np.array(enc_vol.decrypt())[:7]
                diagnostics = MentalHealthDiagnostics(depression_th=8.0, instability_th=150.0)
                diagnostics.analyze_and_render(plain_sum, plain_vol, days=days)
                
            except Exception as e:
                st.error(f"Decryption Failed: {e}")


def main():
    st.set_page_config(page_title="FHE Emotion (Streamlit)", layout="wide")
    init_session_state()
    client = get_client()
    # Auto-load key if present on disk
    if st.session_state.key_id is None:
        try:
            ctx, key_id, _ = ensure_client_context()
            set_key_info(key_id, ctx)
        except Exception:
            pass
    if st.session_state.jwt_token:
        client.token = st.session_state.jwt_token

    page = st.sidebar.radio("Navigation", ["Auth", "Key setup", "Today", "History"])

    if page == "Auth":
        render_auth(client)
    elif page == "Key setup":
        render_key_setup(client)
    elif page == "Today":
        render_today(client)
    elif page == "History":
        render_history(client)


if __name__ == "__main__":
    main()
