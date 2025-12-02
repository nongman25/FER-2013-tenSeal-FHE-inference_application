# Streamlit Frontend – FHE Emotion (End-to-End)

이 디렉터리는 React 대신 **Streamlit**으로 작성된 클라이언트입니다. 암호화/복호화/키 관리를 모두 클라이언트에서 수행하고, FastAPI 백엔드는 공개/평가기 키와 암호문만 취급합니다.

## 구조
```
client/
├── requirements.txt          # streamlit + requests + tenseal + torch
└── streamlit_app/
    ├── app.py                # Streamlit UI (Auth, Key setup, Today, History)
    ├── api_client.py         # FastAPI 호출 래퍼 (requests)
    ├── config.py             # 백엔드 URL, 키 경로 설정
    ├── fhe_keys.py           # CKKS 컨텍스트 생성/저장/로드 (비밀키 포함 로컬 저장)
    ├── preprocessing.py      # 48x48 그레이스케일 정규화
    ├── state.py              # session_state 헬퍼
    └── keys/                 # 로컬 키/메타 저장 위치 (gitignore)
```

## 실행 방법
```bash
cd prototype_app/client
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cd streamlit_app
streamlit run app.py
```
- 환경 변수 `BACKEND_BASE_URL`로 FastAPI 주소를 지정할 수 있습니다(기본 `http://localhost:8000`).
- 키 저장 경로를 바꾸려면 `FHE_KEY_DIR` 환경 변수로 지정하세요.

## 동작 흐름 (E2E FHE)
1. **로그인/회원가입**: `/auth/*` 엔드포인트 사용, JWT 획득.
2. **키 생성/등록**:
   - 최초 실행: `fhe_keys.ensure_client_context()`가 CKKS 컨텍스트를 생성하고 비밀키 포함 버전은 로컬 `keys/`에 저장, 비밀키 없는 eval 컨텍스트를 `/he/register-key`로 전송.
   - 이후 실행: 기존 키 로드, 재등록 생략.
3. **오늘 감정 분석**:
   - 업로드 이미지를 48×48 그레이스케일 + 정규화 → `ts.im2col_encoding`으로 암호화.
   - `/emotion/analyze-today`로 암호문 전송, 서버는 FHE CNN 연산 후 암호문 로짓 반환.
   - 클라이언트가 복호화 후 softmax → 라벨/확률 시각화.
4. **N일 히스토리**:
   - `/emotion/history-raw`에서 암호문 로짓 리스트 수신.
   - 클라이언트가 모두 복호화해 라벨 빈도/타임라인을 로컬에서 계산 후 출력.

## 주의 사항
- TenSEAL/torch를 클라이언트와 서버 모두 설치해야 진짜 FHE 경로가 동작합니다.
- 백엔드에는 **비밀키를 보내지 마세요**. `fhe_keys.py`는 비밀키가 포함된 컨텍스트를 로컬 파일로만 저장합니다.
- 정규화 통계(`NORMALIZATION_MEAN/STD`)는 학습 시점과 맞춰야 합니다. 현재 값은 `models/normalization_stats.json`과 동일한 기본값입니다.
