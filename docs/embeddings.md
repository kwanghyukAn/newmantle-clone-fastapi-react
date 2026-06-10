# Embedding Import Notes

## Chosen Source

The selected source is the official fastText Korean Common Crawl + Wikipedia model:

- `cc.ko.300.vec.gz`
- Published by fastText under the "Word vectors for 157 languages" release

Why this source:

- official distribution from fastText
- broad Korean vocabulary coverage
- subword-aware vectors, which are useful for Korean surface variation
- documented training recipe and paper

The text-vector archive at `cc.ko.300.vec.gz` is currently served at `1,267,506,825` bytes according to a HEAD check on June 10, 2026.

## Current State

The app currently uses a tiny seed vocabulary in:

- `backend/app/data/korean_nouns_seed.json`

This is only for local prototype behavior. It is not enough for a real Semantle-style experience.

## Import Contract

### fastText `.vec` example

The first line is the header:

```text
2000000 300
```

Each later line is:

```text
사과 0.123 0.532 ...
```

## Recommended Preparation Command

The workspace now includes a downloader + converter for the official source:

```bash
cd /path/to/workspace
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
python3 backend/scripts/prepare_fasttext_ko.py \
  --max-vocab 200000 \
  --answer-whitelist backend/app/data/answer_whitelist_seed.txt \
  --answer-blacklist backend/app/data/answer_blacklist_seed.txt
```

This will:

1. download the official `cc.ko.300.vec.gz` file into `backend/.cache/`
2. filter noun-like Hangul vocabulary
3. optionally intersect with a noun lexicon
4. write app-ready files into `backend/app/data/`

If a previous download was interrupted, the preparer now checks the cached file size and automatically restarts the download when the server rejects the stored byte range with `416 Requested Range Not Satisfied`.

The preparer now resolves its default cache/output paths from the repository root, so it behaves consistently even when launched from a different working directory.

Generated files:

- `backend/app/data/fasttext_ko_words.json`
- `backend/app/data/fasttext_ko_vectors.npz`
- `backend/app/data/fasttext_ko_answer_words.json`
- `backend/app/data/fasttext_ko_metadata.json`

## Optional Size Tuning

```bash
python3 backend/scripts/prepare_fasttext_ko.py --max-vocab 30000
python3 backend/scripts/prepare_fasttext_ko.py --max-vocab 250000 --min-word-length 1 --max-word-length 12
python3 backend/scripts/prepare_fasttext_ko.py --noun-lexicon /path/to/full_korean_noun_lexicon.txt
```

The default is now `200000` words. Lower values reduce disk/memory cost; higher values improve coverage.
The answer pool defaults to `15000` words and is written separately from the allowed-guess pool.
Single-character nouns can now be kept in the guess pool by default.
For gameplay quality, the allowed-guess pool should remain broad. A very small noun lexicon is appropriate only for curated answer selection, not for limiting every guess.

## Practical Note

The official fastText source does not include POS tags. In this workspace, the preparer currently applies a conservative Korean-word heuristic to keep noun-like Hangul tokens and stores vectors as compressed `float32` arrays instead of huge JSON blobs.

For production quality, the next refinement should be:

1. intersect the fastText vocabulary with a Korean noun lexicon
2. normalize inflected or particle-attached forms out of the candidate list
3. curate the answer-word pool separately from the allowed-guess pool

## Recommended Next Move

Once you choose the actual Korean embedding source, point the app config to the generated full dataset and then re-tune:

1. answer-word candidate filtering
2. rank cutoff rules
3. hint selection
4. duplicate/variant normalization
