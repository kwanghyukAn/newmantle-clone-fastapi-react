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
  --noun-lexicon backend/app/data/noun_lexicon_seed.txt \
  --answer-whitelist backend/app/data/answer_whitelist_seed.txt \
  --answer-blacklist backend/app/data/answer_blacklist_seed.txt
```

This downloads the official fastText Korean `cc.ko.300.vec.gz` archive, filters noun-like Hangul words, and generates app-ready files in `backend/app/data/`.

If the download was interrupted earlier, the script now auto-recovers from `416 Requested Range Not Satisfied` by resetting the stale cache and retrying.

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
