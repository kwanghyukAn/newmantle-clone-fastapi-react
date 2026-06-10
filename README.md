# Newmantle Clone Workspace

## Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Prepare real Korean embeddings

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
python3 backend/scripts/prepare_fasttext_ko.py \
  --max-vocab 200000 \
  --answer-whitelist backend/app/data/answer_whitelist_seed.txt \
  --answer-blacklist backend/app/data/answer_blacklist_seed.txt
```

This downloads the official fastText Korean `cc.ko.300.vec.gz` archive, filters noun-like Hangul words, and generates app-ready files in `backend/app/data/`.

기본값도 넓혀 두었습니다. 이제 허용 추측 풀은 기본 `200,000`개까지 유지하고, 한 글자 명사도 포함할 수 있습니다.

If the download was interrupted earlier, the script now auto-recovers from `416 Requested Range Not Satisfied` by resetting the stale cache and retrying.

`--noun-lexicon` is optional. For real gameplay coverage, do not use the tiny seed lexicon as the default filter because it sharply reduces the allowed guess pool.

If you pass a very small noun lexicon, the preparer now refuses by default. That is intentional: the allowed guess pool should stay broad, while the answer pool is curated separately.

## Run frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Static build deployment

프런트를 정적 빌드한 뒤 FastAPI가 직접 서빙할 수 있습니다.

```bash
cd frontend
npm install
npm run build
```

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

이 상태에서는 프런트와 API를 모두 `http://서버IP:8000` 하나로 접근합니다. `frontend/dist`가 존재하면 FastAPI가 `/`와 `/assets/*`를 직접 서빙합니다.

## PWA installability

이 프런트는 `manifest.webmanifest`와 `service worker`를 포함하므로 PWA 설치형으로 동작할 수 있습니다.

중요:

- `localhost`에서는 설치 테스트가 가능합니다.
- 다른 PC나 모바일에서 실제로 `설치` 버튼이 보이게 하려면 보통 `HTTPS`가 필요합니다.
- 단순 `http://서버IP:8000` 주소는 대부분의 브라우저에서 설치형 조건을 만족하지 못합니다.

## Access from another PC

If the server PC IP is `192.168.0.10`, open:

- Frontend dev mode: `http://192.168.0.10:5173`
- Frontend static deployment: `http://192.168.0.10:8000`
- Backend health: `http://192.168.0.10:8000/health`

The frontend now uses relative `/api` requests with Vite proxy in dev mode, so same-server and same-network access avoids the old localhost CORS mismatch.

## Current status

- FastAPI backend scaffolded
- React frontend scaffolded
- Local seed vocabulary wired into a cosine-similarity engine
- Official fastText Korean preparation pipeline included
- Room create/join/guess/state flow implemented with SQLite persistence
- Room live updates delivered over WebSocket
- Daily hint / initial-hint / give-up / share-ready flow included

## Important limitation

The current checked-in vocabulary is still intentionally tiny so the workspace runs immediately without a 1.2GB download. On the target machine, run the preparation command above to switch the app to the official fastText Korean dataset automatically.

Details are in [docs/embeddings.md](/Users/kwanghyukan/Documents/Codex/2026-06-10-pc-https-www-newmantle-kr-fast/docs/embeddings.md:1), and the preparation script is [backend/scripts/prepare_fasttext_ko.py](/Users/kwanghyukan/Documents/Codex/2026-06-10-pc-https-www-newmantle-kr-fast/backend/scripts/prepare_fasttext_ko.py:1).

A fuller operator guide is in [reader.md](/Users/kwanghyukan/Documents/Codex/2026-06-10-pc-https-www-newmantle-kr-fast/reader.md:1).
