from __future__ import annotations

import argparse
import gzip
import json
import re
import urllib.request
from pathlib import Path

import numpy as np


FASTTEXT_KO_VEC_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ko.300.vec.gz"
JOSA_ENDINGS = (
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "로",
    "과",
    "와",
    "도",
    "만",
    "께",
    "에서",
    "까지",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download official fastText Korean vectors and convert them to an app-friendly filtered dataset."
    )
    parser.add_argument(
        "--download-url",
        default=FASTTEXT_KO_VEC_URL,
        help="Override the official fastText Korean vec.gz URL.",
    )
    parser.add_argument(
        "--cache-path",
        default="backend/.cache/cc.ko.300.vec.gz",
        help="Path to store the downloaded vec.gz file.",
    )
    parser.add_argument(
        "--output-dir",
        default="backend/app/data",
        help="Directory where app-ready data files will be written.",
    )
    parser.add_argument(
        "--max-vocab",
        type=int,
        default=60000,
        help="Maximum number of noun-like words to retain.",
    )
    parser.add_argument(
        "--noun-lexicon",
        default="",
        help="Optional newline-delimited noun lexicon file. When provided, only words in this lexicon are kept.",
    )
    parser.add_argument(
        "--max-answer-vocab",
        type=int,
        default=8000,
        help="Maximum number of answer candidates to retain from the filtered vocabulary.",
    )
    return parser.parse_args()


def is_hangul_word(word: str) -> bool:
    return bool(re.fullmatch(r"[가-힣]+", word))


def looks_like_noun(word: str) -> bool:
    if not is_hangul_word(word):
        return False
    if len(word) < 2 or len(word) > 8:
        return False
    if any(word.endswith(ending) and len(word) > len(ending) + 1 for ending in JOSA_ENDINGS):
        return False
    return True


def looks_like_answer_candidate(word: str) -> bool:
    if not looks_like_noun(word):
        return False
    if len(word) < 2 or len(word) > 5:
        return False
    blocked_suffixes = ("하다", "되다", "같다", "스럽다", "적인")
    if word.endswith(blocked_suffixes):
        return False
    return True


def load_noun_lexicon(path: str) -> set[str]:
    if not path:
        return set()
    lexicon_path = Path(path)
    return {
        line.strip()
        for line in lexicon_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and is_hangul_word(line.strip())
    }


def download_with_resume(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing_size = destination.stat().st_size if destination.exists() else 0
    request = urllib.request.Request(url)
    if existing_size:
        request.add_header("Range", f"bytes={existing_size}-")
    with urllib.request.urlopen(request) as response:
        if response.status == 200 and existing_size:
            destination.unlink()
            existing_size = 0
        mode = "ab" if existing_size else "wb"
        with destination.open(mode) as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)


def convert_vec_gz(
    source: Path,
    output_dir: Path,
    max_vocab: int,
    noun_lexicon: set[str],
    max_answer_vocab: int,
) -> None:
    words: list[str] = []
    vectors: list[list[float]] = []
    seen: set[str] = set()
    answer_words: list[str] = []

    with gzip.open(source, "rt", encoding="utf-8", newline="\n", errors="ignore") as handle:
        header = handle.readline()
        if not header:
            raise RuntimeError("empty fastText vector file")

        for line in handle:
            pieces = line.rstrip().split(" ")
            if len(pieces) < 11:
                continue
            word = pieces[0]
            if not looks_like_noun(word):
                continue
            if noun_lexicon and word not in noun_lexicon:
                continue
            normalized = word.lower()
            if normalized in seen:
                continue
            try:
                vector = [float(value) for value in pieces[1:]]
            except ValueError:
                continue
            seen.add(normalized)
            words.append(word)
            vectors.append(vector)
            if len(answer_words) < max_answer_vocab and looks_like_answer_candidate(word):
                answer_words.append(word)
            if len(words) >= max_vocab:
                break

    output_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_dir / "fasttext_ko_vectors.npz", vectors=np.asarray(vectors, dtype=np.float32))
    (output_dir / "fasttext_ko_words.json").write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    (output_dir / "fasttext_ko_answer_words.json").write_text(
        json.dumps(answer_words, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "fasttext_ko_metadata.json").write_text(
        json.dumps(
            {
                "source": FASTTEXT_KO_VEC_URL,
                "selected_words": len(words),
                "selected_answer_words": len(answer_words),
                "dimension": len(vectors[0]) if vectors else 0,
                "filter": "hangul noun-like heuristic",
                "lexicon_intersection": bool(noun_lexicon),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    cache_path = Path(args.cache_path)
    output_dir = Path(args.output_dir)
    noun_lexicon = load_noun_lexicon(args.noun_lexicon)
    print(f"downloading official fastText Korean vectors to {cache_path}")
    download_with_resume(args.download_url, cache_path)
    print(f"converting to filtered app dataset in {output_dir}")
    convert_vec_gz(cache_path, output_dir, args.max_vocab, noun_lexicon, args.max_answer_vocab)
    print("done")


if __name__ == "__main__":
    main()
