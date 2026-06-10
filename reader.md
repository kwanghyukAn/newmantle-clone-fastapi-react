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
- 근접 힌트 / 초성 힌트 / 포기 / 결과 공유
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
  --answer-whitelist backend/app/data/answer_whitelist_seed.txt \
  --answer-blacklist backend/app/data/answer_blacklist_seed.txt
```

이 명령은 다음을 수행합니다.

1. 공식 fastText 한국어 `cc.ko.300.vec.gz` 다운로드
2. 한국어 noun-like 토큰 필터링
3. 선택적으로 명사 사전과 교차
4. 정답 후보 화이트리스트/블랙리스트 적용
5. 앱이 읽을 수 있는 압축 벡터 파일 생성

주의:

- 기본 운영 명령에서는 `noun_lexicon_seed.txt`를 넣지 않는 편이 맞습니다.
- 그 파일은 너무 작아서 허용 추측 단어 풀이 지나치게 줄어듭니다.
- `--noun-lexicon`은 더 큰 실제 명사 사전이 생겼을 때만 쓰는 옵션으로 보는 게 맞습니다.
- 현재 스크립트는 작은 lexicon으로 전체 허용 단어 풀을 제한하려고 하면 기본적으로 중단합니다.

생성 결과:

- `backend/app/data/fasttext_ko_words.json`
- `backend/app/data/fasttext_ko_vectors.npz`
- `backend/app/data/fasttext_ko_answer_words.json`
- `backend/app/data/fasttext_ko_metadata.json`

이전에 다운로드가 중단됐던 환경에서는 `416 Requested Range Not Satisfied`가 날 수 있었는데, 현재 스크립트는 캐시 크기를 검사하고 필요하면 `backend/.cache/cc.ko.300.vec.gz`를 자동으로 다시 받아오도록 보강되어 있습니다.

### 3. 백엔드 실행

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

기본 주소:

- `http://127.0.0.1:8000`

### 4. 프런트 실행

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

기본 주소:

- `http://127.0.0.1:5173`

같은 네트워크의 다른 PC에서는 서버 PC IP로 접속합니다.

- 예시 프런트: `http://서버IP:5173`
- 예시 백엔드 헬스체크: `http://서버IP:8000/health`

## 배포용 정적 빌드

운영 배포에서는 Vite 개발 서버를 띄우지 않고, 프런트를 정적 빌드한 뒤 FastAPI가 직접 서빙하는 구조를 권장합니다.

### 1. 프런트 빌드

```bash
cd frontend
npm install
npm run build
```

이 명령으로 `frontend/dist`가 생성됩니다.

### 2. 백엔드 실행

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

이제 아래 주소 하나만 열면 됩니다.

- `http://서버IP:8000`

현재 `backend/app/main.py`는 `frontend/dist/index.html`과 `frontend/dist/assets/*`가 존재하면 이를 직접 서빙합니다. 그래서 운영 환경에서는 프런트와 API가 같은 origin으로 붙고, CORS를 별도로 의식할 일이 크게 줄어듭니다.

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

## 싱글 플레이 UX

현재 싱글 플레이에는 아래 흐름이 포함되어 있습니다.

- 일반 추측 제출
- 근접 힌트
- 초성 힌트
- 포기하기 후 정답 공개
- 공유용 결과 문구 생성

이 상태 값 일부는 SQLite의 일일 세션 메타에 저장됩니다.

## 어휘 품질 제어

현재 프로젝트는 세 가지 텍스트 파일로 answer pool 품질을 조정할 수 있습니다.

- `backend/app/data/noun_lexicon_seed.txt`
- `backend/app/data/answer_whitelist_seed.txt`
- `backend/app/data/answer_blacklist_seed.txt`

권장 방식:

1. `noun_lexicon_seed.txt` 는 "허용할 명사" 기준
2. `answer_whitelist_seed.txt` 는 "정답으로 특히 쓰고 싶은 단어" 기준
3. `answer_blacklist_seed.txt` 는 "정답에서 빼고 싶은 단어" 기준

실서비스로 갈수록 이 세 파일은 더 큰 사전/운영 데이터로 교체하면 됩니다.

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
5. 운영 배포 시 `frontend/dist` 생성

원본 `cc.ko.300.vec.gz`는 2026-06-10 확인 기준 약 `1.27GB`입니다.

## GitHub 관련

현재 원격 저장소:

- `https://github.com/kwanghyukAn/newmantle-clone-fastapi-react`
