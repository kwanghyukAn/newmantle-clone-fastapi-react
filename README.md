# Newmantle Clone Workspace

## Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
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

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

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
