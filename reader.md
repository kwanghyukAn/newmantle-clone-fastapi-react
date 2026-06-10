# Reader Guide

## 목적

이 워크스페이스는 `newmantle.kr`류의 한국어 의미 유사도 단어 추측 게임을 로컬에서 재현하기 위한 프로젝트입니다.

기술 스택:

- Backend: FastAPI
- Frontend: React + Vite
- Persistence: SQLite
- Realtime: WebSocket
- Embeddings: 공식 fastText 한국어 벡터를 후처리한 로컬 데이터

## 현재 포함된 것

- 바로 실행 가능한 프로토타입
- 싱글 플레이
- 방 생성 / 입장 / 실시간 랭킹
- SQLite 저장
- 공식 fastText 한국어 데이터 준비 스크립트

## 현재 저장소에 포함되지 않은 것

용량 문제 때문에 아래 대형 데이터는 저장소에 포함하지 않았습니다.

- `cc.ko.300.vec.gz`
- 후처리된 대용량 벡터 산출물

이 데이터는 대상 환경에서 직접 생성해야 합니다.

## 필요한 환경

권장:

- Python 3.11+
- Node.js 20+ 권장
- npm

참고:

- 현재 저장소는 Node 16 환경에서도 `Vite 4` 기준으로 빌드는 통과합니다.
- 다만 장기적으로는 Node 20 이상을 권장합니다.

## 처음 실행 순서

### 1. 백엔드 가상환경 생성

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 실제 한국어 임베딩 준비

루트 디렉터리에서:

```bash
source backend/.venv/bin/activate
python3 backend/scripts/prepare_fasttext_ko.py \
  --noun-lexicon backend/app/data/noun_lexicon_seed.txt
```

이 명령은 다음을 수행합니다.

1. 공식 fastText 한국어 `cc.ko.300.vec.gz` 다운로드
2. 한국어 noun-like 토큰 필터링
3. 선택적으로 명사 사전과 교차
4. 앱이 읽을 수 있는 압축 벡터 파일 생성

생성 결과:

- `backend/app/data/fasttext_ko_words.json`
- `backend/app/data/fasttext_ko_vectors.npz`
- `backend/app/data/fasttext_ko_answer_words.json`
- `backend/app/data/fasttext_ko_metadata.json`

### 3. 백엔드 실행

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

기본 주소:

- `http://127.0.0.1:8000`

### 4. 프런트 실행

```bash
cd frontend
npm install
npm run dev
```

기본 주소:

- `http://127.0.0.1:5173`

## 데이터 관련 설명

### 왜 fastText를 선택했는가

- 공식 배포본이 있다
- 한국어 어휘 범위가 넓다
- subword 기반이라 한국어 표면형 변화에 상대적으로 강하다
- 회사 환경에서 재현 가능하다

### 왜 그대로 쓰지 않고 후처리하는가

원본을 그대로 쓰면:

- 단어 수가 너무 많다
- 조사 붙은 표면형, 불필요한 토큰이 많다
- 정답 후보 풀로 쓰기에는 품질이 고르지 않다

그래서 현재는 두 단계로 나눴습니다.

1. `allowed guess pool`
2. `answer candidate pool`

정답 후보는 더 짧고 보편적인 명사 위주로 따로 추립니다.

### 더 좋은 품질로 가려면

다음 자료가 있으면 품질이 더 좋아집니다.

- 한국어 명사 사전
- 빈도 정보가 있는 일반명사 목록
- 서비스에서 금지할 고유명사 / 비속어 / 노이즈 토큰 목록

## 주요 파일

- `backend/app/main.py`
- `backend/app/services/game_engine.py`
- `backend/app/services/embedding_store.py`
- `backend/app/services/storage.py`
- `backend/scripts/prepare_fasttext_ko.py`
- `frontend/src/App.tsx`
- `frontend/src/pages/SoloPage.tsx`
- `frontend/src/pages/RoomPage.tsx`

## 회사 환경에서 필요한 것

최소한 아래만 있으면 됩니다.

1. Python / Node 설치
2. 인터넷 연결
3. fastText 원본 다운로드 허용
4. 약간의 디스크 여유 공간

원본 `cc.ko.300.vec.gz`는 2026-06-10 확인 기준 약 `1.27GB`입니다.

## GitHub 관련

이 저장소는 아직 로컬 폴더 상태일 수 있습니다. GitHub에 올리려면:

1. `git init`
2. 원격 저장소 생성
3. 커밋
4. push

Codex가 GitHub 인증 상태에 접근 가능하면 이 단계도 대신 진행할 수 있습니다.
