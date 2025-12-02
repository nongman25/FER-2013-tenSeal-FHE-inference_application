# Frontend (React + TypeScript) – FHE Emotion Prototype

브라우저에서 이미지 업로드·전처리 → (암호화 가정) → FastAPI 백엔드 호출 → 암호화 결과(가정) 복호화/표시까지의 흐름을 담은 SPA입니다. 모든 HE 세부사항은 `lib/crypto/` 추상화에 캡슐화되어 있으며, 나머지 UI/비즈니스 레이어는 암호화 포맷을 알지 않습니다.

## 주요 기능
- 로그인/회원가입(JWT) UI, 토큰 저장/주입
- 이미지 업로드 → 48×48 그레이스케일/정규화(평문) → “암호문” 생성 → `/emotion/analyze-today` 호출
- 암호화 응답(가정) 복호화 후 감정 라벨/확률 표시
- N일 분석 요청 `/emotion/history` → 복호화(가정) → 결과 렌더
- 키 관리: 로컬스토리지에 키페어 저장/불러오기(스텁), 내보내기/가져오기 메서드 제공

## 디렉터리 구조
```
frontend/
├── src/
│   ├── app/                 # 앱 셸, 라우팅, 전역 스타일
│   ├── features/
│   │   ├── auth/            # 로그인/회원가입 UI + 훅 + API 클라이언트
│   │   └── emotion/         # 업로드/분석/히스토리 UI + 훅 + API 클라이언트
│   ├── lib/
│   │   ├── http/            # fetch 래퍼, JWT 헤더 주입
│   │   └── crypto/          # 프런트 HE 추상화(fheClient), 전처리
│   └── types/               # DTO 타입 정의
├── package.json, tsconfig*, vite.config.ts
└── index.html
```

## 빠른 실행
```bash
cd prototype_app/frontend
npm install
VITE_API_BASE_URL=http://localhost:8000 npm run dev    # 백엔드 주소 맞춰 설정
```
- 기본 포트: 5173. 백엔드 CORS 허용 필요 시 서버 설정 수정.

## 설정 포인트
- `.env` 또는 실행 시 `VITE_API_BASE_URL` 환경 변수로 백엔드 베이스 URL 지정 (미설정 시 `http://localhost:8000`)
- 로컬스토리지 키: `fhe-emotion-keypair`, `fhe-auth-state`
- 디자인: 전역 스타일 `src/app/styles.css`에서 색상/폰트 커스터마이즈 가능

## 암호화(HE) 관련 주의와 구현 계획
- 현재 `lib/crypto/fheClient.ts`는 **실제 동형암호가 아닙니다**. 이유:
  - 브라우저에 TenSEAL/CKKS 런타임이 없고, 직렬화 포맷/키 교환이 미정
  - 프로토타입 속도/의존성 최소화를 위해 base64(JSON) 직렬화로 “암호문처럼” 취급
- 현재 동작:
  - `encryptPreprocessedImage`: 정규화된 픽셀 배열을 JSON→base64 인코딩 후 전송
  - `decryptPrediction` / `decryptHistoryReport`: base64 디코딩 후 JSON 파싱
  - 백엔드도 동일 스텁을 사용해 평문 모델을 돌려 암호문인 척 반환
- 실제 HE로 전환하려면:
  1. 브라우저 혹은 프런트 모듈에서 CKKS 공개키/컨텍스트를 로드해 암호화 가능하도록 WASM/Native 브리지 또는 백엔드 프록시 암호화 API를 설계
  2. 직렬화 포맷(예: `context.serialize()` / `ckks_vector.serialize()`)을 정의하고, `encryptPreprocessedImage`에서 해당 포맷을 생성
  3. 백엔드 `HEEmotionEngine.run_encrypted_inference`에서 그 포맷을 역직렬화 → TenSEAL `CKKSVector` → FHE CNN 실행 → 결과를 동일 포맷으로 직렬화해 응답
  4. `decryptPrediction`에서 개인키로 복호화할 수 있게 프라이빗 키는 클라이언트에만 저장/보호
  5. N일 분석은 Enc(summary) 리스트에 대해 HE 연산(빈도/전이/run-length 등)을 정의하고 동일 직렬화 포맷을 유지

## 전처리 파이프라인
- `lib/crypto/preprocessing.ts`
  - 48×48 리사이즈 + 루미넌스 그레이스케일 (0.299R + 0.587G + 0.114B)
  - 정규화: `(pixel/255 - mean) / std` (`NORMALIZATION_MEAN=0.507`, `NORMALIZATION_STD=0.255`) — 추후 백엔드 `normalization_stats.json`과 동기화 필요
  - 원본/그레이스케일 미리보기 DataURL 제공

## 라우팅/흐름
- `/login`, `/register`: 인증 화면
- `/emotion/today`: 파일 업로드 → 전처리 → 암호화(가정) → API 호출 → 복호화(가정) 결과 표시
- `/emotion/history`: N일 조회 → 복호화(가정) 결과 JSON 렌더

## 기타
- JWT는 `httpClient`에서 자동 헤더 주입
- UI 상태: `useAuth`, `useEmotionFlow` 훅에서 로딩/에러 관리
- 키 내보내기/가져오기 API는 제공되지만 UI 버튼은 아직 없으므로 필요 시 컴포넌트에 연결하세요.
