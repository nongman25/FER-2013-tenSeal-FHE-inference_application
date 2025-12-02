# Backend (FastAPI) – FHE Emotion Prototype

프라이버시 친화 감정 인식 프로토타입의 FastAPI 백엔드입니다. 기존 FHE 모델/코드(`he/`, `models/`)를 **서비스 계층**에서 어댑터로 감싸고, JWT 인증/DB/도메인 로직을 얇은 라우터로 노출합니다.

## 주요 기능
- `/auth` : 회원 가입, 로그인(JWT 발급)
- `/emotion/analyze-today` : 암호화(가정)된 이미지 입력 → 암호화(가정)된 추론 결과 반환 + 일자별 Enc(summary) 저장
- `/emotion/history` : 최근 N일 Enc(summary) 가져와(현재는 스텁) 반환
- `/health` : 헬스 체크
- 레이어 분리: `schemas`(DTO) ↔ `repositories`(DB) ↔ `services`(도메인) ↔ `api`(HTTP). HE 로직은 `services/he_service.py`에만 위치.

## 디렉터리 구조
```
backend/
└── app/
    ├── core/                # 설정, DB, 보안(JWT, bcrypt)
    ├── models/              # SQLAlchemy ORM (user, emotiondata)
    ├── schemas/             # Pydantic DTO
    ├── repositories/        # DB 접근 레이어
    ├── services/            # 도메인 서비스, HE 어댑터
    ├── api/                 # FastAPI 라우트
    └── main.py              # 앱 팩토리, 라우터/서비스 등록
```

## 빠른 실행
```bash
cd prototype_app/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .           # 기본 포트 8000
```

## 환경 변수 (.env 예시)
```
EMOTION_DB_HOST=localhost
EMOTION_DB_PORT=3306
EMOTION_DB_NAME=emotiondb
EMOTION_DB_USER=root
EMOTION_DB_PASSWORD=0524
EMOTION_DB_CHARSET=utf8mb4
EMOTION_DB_TIMEZONE=Asia/Seoul

JWT_SECRET_KEY=change-this-dev-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

EMOTION_ANALYSIS_DAYS=10
```

### DB 드라이버
- `config.sqlalchemy_url()`은 `mysql+pymysql://...`을 사용합니다. MySQL 접근 권한과 스키마를 미리 생성해 주세요.
- 다른 드라이버를 쓰고 싶다면 `core/config.py`의 URL 생성 로직과 `requirements.txt`를 함께 수정하세요.

## 라우트/주입 흐름
- 라우터에서 `get_db()`로 세션 주입 → 서비스 호출
- 서비스는 저장소/HE 어댑터만 의존, HTTP나 JWT에 비침투
- `app.state.*`에 서비스 인스턴스 바인딩 (`main.py`)

## HE(암호화) 관련 주의
- 현재 `services/he_service.py`는 **스텁(stub) 직렬화**를 사용합니다.
  - 프론트에서 오는 `ciphertext`를 base64(JSON)로 가정하고 평문 모델 추론 → 다시 base64(JSON)로 인코딩해 반환
  - 이유: 브라우저에서 TenSEAL/CKKS를 직접 돌릴 수 없고, 실제 직렬화 포맷/키 교환이 정해지지 않았기 때문
- 실제 동형암호로 전환하려면:
  1. **클라이언트 측**에서 CKKS 컨텍스트/공개키 기반 직렬화 포맷을 정의하고, `fheClient`가 TenSEAL 호환 암호문을 생성하도록 구현
  2. **서버 측** `HEEmotionEngine.run_encrypted_inference`에서 해당 직렬화 포맷을 역직렬화하여 `ts.CKKSVector`로 변환 후 `PackedEncryptedCNNRunner` 실행
  3. 추론 결과도 동일 포맷으로 직렬화해 반환, 클라이언트는 개인키로 복호화
  4. N일 분석(`analysis_service.py`)에 필요한 암호문 집계 연산(빈도, 전이, run-length 등)을 HE 방식으로 구현
- 그 전까지는 “암호문처럼 보이는” base64 JSON을 오고가며, 서버는 실제 비밀키를 갖지 않는다는 규칙만 유지합니다.

## 설정/변경 포인트
- DB 접속 정보와 JWT 시크릿은 **반드시 .env로 설정**
- CORS 허용 도메인: 필요 시 `main.py`의 `allow_origins` 수정
- 패스워드 해시는 bcrypt(`passlib[bcrypt]`), 필요 시 `core/security.py` 조정
- 모델 마이그레이션 도구(Alembic)는 포함되지 않았으므로 스키마 변경 시 수동 반영 필요
