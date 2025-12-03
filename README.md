# FHE Emotion Prototype – 독립 실행 가능 프로토타입

## ⚠️ 중요: 완전 독립 실행 가능
이 `prototype_app` 디렉토리는 **루트 프로젝트(`fhe_emotion`)에 의존하지 않습니다**.
- ✅ 필요한 모든 코드가 `prototype_app` 내부에 포함됨
- ✅ FHE 엔진, 모델, 전처리 로직이 모두 복사됨
- ✅ 이 디렉토리만으로 배포/실행 가능

## 개요
동형암호(FHE) 기반 감정 인식 풀스택 프로토타입입니다.
- **프론트엔드 (Streamlit, Python)**: 키 생성/보관, 이미지 전처리, 클라이언트 암호화/복호화, 단일일 추론 및 N일 히스토리 UI.
- **백엔드 (FastAPI, Python)**: 인증, 키 등록, 암호문 추론, 암호문 히스토리 조회. 비밀키는 보지 않습니다.
- **HE 엔진 (TenSEAL + Torch)**: 기존 모델 `he_cnn_fer2013_enhanced.pt`(백엔드 내부 `backend/app/inference_model/`에 사본)과 클라이언트가 제공한 평가 컨텍스트 사용.

향후 팀원이 서버 측 N일 암호문 분석을 구현할 수 있도록 현재 API/흐름/확장 포인트를 정리합니다.

## 디렉터리 구조
```
prototype_app/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 앱
│   │   ├── core/                      # 설정, DB, JWT 보안
│   │   ├── models/                    # User, EmotionData ORM
│   │   ├── schemas/                   # Pydantic DTO
│   │   ├── repositories/              # DB 접근 계층
│   │   ├── services/
│   │   │   ├── he_service.py         # FHE 엔진 (독립)
│   │   │   ├── emotion_service.py    # 단일일 추론
│   │   │   └── analysis_service.py   # N일 분석 (확장 포인트)
│   │   ├── api/                      # REST 엔드포인트
│   │   ├── fhe_core/                 # ✅ FHE 코어 로직 (루트에서 복사)
│   │   │   ├── fhe_inference.py
│   │   │   ├── fhe_cnn.py
│   │   │   └── tenseal_context.py
│   │   └── inference_model/          # ✅ 모델 파일 (로컬 사본)
│   │       ├── he_cnn_fer2013_enhanced.pt
│   │       └── normalization_stats.json
│   └── requirements.txt
├── client/
│   ├── streamlit_app/
│   │   ├── app.py                    # Streamlit UI
│   │   ├── api_client.py             # HTTP 클라이언트
│   │   ├── fhe_keys.py               # 키 생성/로드
│   │   ├── preprocessing.py          # 이미지 전처리
│   │   ├── config.py
│   │   └── keys/                     # 클라이언트 키 저장소 (gitignore)
│   └── requirements.txt
└── README.md
```

### ✅ 독립성 확인사항
- `backend/app/fhe_core/`: 루트 `he/`, `models/` 모듈을 복사하여 독립
- `backend/app/inference_model/`: 모델 파일 로컬 사본
- 모든 import가 `app.` prefix로 상대 경로 사용
- `DATA_DIR`(테스트용)은 프로덕션에서 사용 안 함

## 백엔드 API
Base URL (dev): `http://localhost:8000`

### Auth
- `POST /auth/register` — `{ user_id, password, email? }`
- `POST /auth/login` — `{ user_id, password }` -> `{ access_token, token_type }`

### HE 키 등록
- `POST /he/register-key` (JWT)  
  body: `{ key_id, eval_context_b64 }`  
  → `he/contexts/{key_id}.seal`에 저장 후 캐시.

### 감정 추론
- `POST /emotion/analyze-today` (JWT)
  ```json
  {
    "ciphertext": "<b64 CKKS ciphertext>",
    "key_id": "<client key id>",
    "date": "YYYY-MM-DD" // 옵션, 미지정 시 서버 오늘 날짜
  }
  ```
  흐름: eval 컨텍스트로 역직렬화 → 암호문 CNN → `{ ciphertext: <b64 logits>, date }` 반환 + DB 저장.

### 히스토리
- `GET /emotion/history-raw?days=N&key_id=...` (JWT)  
  → `{ key_id, days, entries: [{ date, ciphertext }, ...] }` (암호문 리스트)
- `GET /emotion/history` (stub) → placeholder 암호문

### 헬스체크
- `GET /health` -> `{ "status": "ok" }`

## 프론트엔드 동작(Streamlit)
- 키 설정:
  - 최초: CKKS 생성 → 비밀키 포함 컨텍스트 로컬(`fhe-emotion-keypair.seal`), eval 컨텍스트(`fhe-eval-context.seal`) 전송(`/he/register-key`).
  - 이후: 로컬 키 자동 로드, 재등록 생략.
- Today:
  - 날짜 선택 → 업로드 → 전처리 → `ts.im2col_encoding`으로 암호화 → `/emotion/analyze-today` → 복호화/softmax → 라벨/확률 표시.
- History:
  - `/emotion/history-raw` 호출 → 각 암호문 복호화 → 빈도/타임라인 계산 및 표시.

## N일 분석 확장 가이드(서버)
- 대상 파일:
  - `services/analysis_service.py` (`analyze_recent_days(db, user_id, days)`): 현재 최신 enc_prediction 반환. 여기에 HE 집계 호출 추가.
  - `emotion_data_repository.get_recent_enc_predictions`: N일 enc_prediction 조회.
  - `routㄴes_emotion.py` → `/emotion/history`가 `AnalysisService` 사용.
- 구현 아이디어: (이 부분은 ai가 써준거라 그냥 넘기셔도 됩니다.) 
  1) 암호문 요약 포맷 정의  
     - A안: 일별 logits 유지 후 HE-friendly 빈도 연산  
     - B안: 일별 Enc(one-hot) 저장, 동형 덧셈으로 빈도 집계  
  2) `HEEmotionEngine`에 집계 메서드 추가  
     - `aggregate_enc_summaries(enc_list: list[str], key_id: str) -> str` (암호문 집계 결과 반환)  
  3) `AnalysisService.analyze_recent_days`에서 enc_predictions → HE 집계 호출 → 결과 ciphertext 반환  
  4) `/emotion/history-raw`는 계속 클라이언트 복호화용으로 유지, `/emotion/history`는 집계 암호문 반환하도록 확장
- 클라이언트 변경(선택): History 페이지에 `raw`/`aggregated` 모드 스위치 추가, `/emotion/history` 집계 ciphertext 복호화 후 단일 표시.

## 키 파일 역할
- 클라이언트 전용: `fhe-emotion-keypair.seal` (비밀키 포함, 절대 서버 전송 금지)
- 서버 전송: `fhe-eval-context.seal` (비밀키 없는 eval 컨텍스트)
- 메타: `key_meta.json` (`key_id` 저장)
- 서버 보관: `he/contexts/{key_id}.seal` (eval 컨텍스트), `emotiondata.enc_prediction` (LONGTEXT, b64 CKKS ciphertext)

## 제약/주의
- HE 엔진: TenSEAL + torch + 모델 필수, 스텁 없음.
- bcrypt 비밀번호 72바이트 이하(스키마에서 검증).
- 추론 시간이 길 수 있어 클라이언트 HTTP 타임아웃 120s.
- 로깅: 요청 시작(`📥`), 완료(`🚀 ...`), HE 추론(`🤖 ...`), 컨텍스트 로드(`🔑`), DB upsert 에러(길이/예외).

## 빠른 실행(개발)
- Backend:
  ```
  cd prototype_app/backend
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  uvicorn app.main:app --reload --app-dir . --port 8000
  ```
- Client:
  ```
  cd prototype_app/client
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  cd streamlit_app
  streamlit run app.py
  ```
