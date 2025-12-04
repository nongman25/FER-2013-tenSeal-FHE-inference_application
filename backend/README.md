# Backend (FastAPI) – FHE Emotion Prototype

프라이버시 친화 감정 인식 프로토타입의 FastAPI 백엔드입니다. 필요한 FHE 코드/모델 파일은 모두 `backend/app` 내부(`app/fhe_core`, `app/inference_model`)에 포함되어 있으며, JWT 인증/DB/도메인 로직을 얇은 라우터로 노출합니다. Streamlit 프론트가 **키 생성·암호화·복호화**를 담당하고, 백엔드는 공개/평가기 키와 암호문만 취급합니다.

## 주요 기능
- `/auth/*` : 회원 가입, 로그인(JWT 발급)
- `/he/register-key` : 클라이언트가 보낸 **비밀키 없는** TenSEAL 컨텍스트 등록
- `/emotion/analyze-today` : 암호문(ckks_vector) 입력 → FHE CNN 추론 → 암호문 로짓 반환 + DB 저장
- `/emotion/history-raw` : 최근 N일 암호문 로짓 목록 반환 (서버는 복호화하지 않음)
- `/emotion/history` : 기존 스텁형 N일 분석(서버측 암호문 처리 예정)
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
mysql -u root -p
CREATE DATABASE IF NOT EXISTS emotiondb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

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

JWT_SECRET_KEY=change-this-dev-secret # openssl rand -hex 32 터미널에 이거 쳐서 나온 값 입력.
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

EMOTION_ANALYSIS_DAYS=10
```

### DB 드라이버
- `config.sqlalchemy_url()`은 `mysql+pymysql://...`을 사용합니다. MySQL 접근 권한과 스키마를 미리 생성해 주세요.
- 다른 드라이버를 쓰고 싶다면 `core/config.py`의 URL 생성 로직과 `requirements.txt`를 함께 수정하세요.

### TenSEAL/모델
- `requirements.txt`에 `tenseal`, `torch`를 포함했습니다. FHE 경로를 쓰려면 설치가 필요합니다.
- 모델 가중치는 상위 경로 `models/fhe_cnn_fer2013_enhanced.pt`를 그대로 사용합니다.
  - `services/he_service.py`가 `app/fhe_core/fhe_cnn.py`의 파라미터를 불러와 암호문 연산에 씁니다.

## 라우트/주입 흐름
- 라우터에서 `get_db()`로 세션 주입 → 서비스 호출
- 서비스는 저장소/HE 어댑터만 의존, HTTP나 JWT에 비침투
- `app.state.*`에 서비스 인스턴스 바인딩 (`main.py`)

## HE(암호화) 관련 주의
- `services/he_service.py`는 TenSEAL이 설치되어 있고 클라이언트가 보낸 **evaluation-only context**가 등록된 경우, 진짜 CKKS 암호문을 받아 CNN 연산을 수행한 뒤 암호문 로짓을 그대로 반환합니다.
- TenSEAL/torch가 설치되지 않았거나 컨텍스트가 없을 때는 스텁이 동작합니다(디버그용). 프로덕션에서는 반드시 TenSEAL 경로를 사용하세요.
- 컨텍스트 등록: `/he/register-key`에 비밀키 없는 컨텍스트를 base64로 보내면 서버가 `he/contexts/{key_id}.seal`로 저장하고 캐시합니다. 비밀키가 포함된 컨텍스트를 보내면 경고 로그를 남깁니다.

## 설정/변경 포인트
- DB 접속 정보와 JWT 시크릿은 **반드시 .env로 설정**
- CORS 허용 도메인: 필요 시 `main.py`의 `allow_origins` 수정
- 패스워드 해시는 bcrypt(`passlib[bcrypt]`), 필요 시 `core/security.py` 조정
- 모델 마이그레이션 도구(Alembic)는 포함되지 않았으므로 스키마 변경 시 수동 반영 필요
