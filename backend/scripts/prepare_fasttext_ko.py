from __future__ import annotations

import argparse
import gzip
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np


FASTTEXT_KO_VEC_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ko.300.vec.gz"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_PATH = PROJECT_ROOT / "backend" / ".cache" / "cc.ko.300.vec.gz"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "backend" / "app" / "data"
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
        default=str(DEFAULT_CACHE_PATH),
        help="Path to store the downloaded vec.gz file.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
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
        "--allow-small-lexicon",
        action="store_true",
        help="Allow a tiny noun lexicon to restrict the entire guess pool. Disabled by default because it usually harms gameplay.",
    )
    parser.add_argument(
        "--max-answer-vocab",
        type=int,
        default=8000,
        help="Maximum number of answer candidates to retain from the filtered vocabulary.",
    )
    parser.add_argument(
        "--answer-whitelist",
        default="",
        help="Optional newline-delimited list of answer words to prioritize and include when present in vocab.",
    )
    parser.add_argument(
        "--answer-blacklist",
        default="",
        help="Optional newline-delimited list of words to exclude from answer candidates.",
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


def load_word_list(path: str) -> list[str]:
    if not path:
        return []
    list_path = Path(path)
    return [
        line.strip()
        for line in list_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and is_hangul_word(line.strip())
    ]


def resolve_optional_path(path: str) -> str:
    if not path:
        return path
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return str(resolved)


def get_remote_file_size(url: str) -> int | None:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request) as response:
        header = response.headers.get("Content-Length")
        return int(header) if header else None


def download_with_resume(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing_size = destination.stat().st_size if destination.exists() else 0
    remote_size = get_remote_file_size(url)

    if remote_size is not None:
        if existing_size == remote_size:
            print(f"cached archive already complete at {destination}")
            return
        if existing_size > remote_size:
            print(f"cached archive is larger than remote file, resetting {destination}")
            destination.unlink(missing_ok=True)
            existing_size = 0

    request = urllib.request.Request(url)
    if existing_size:
        request.add_header("Range", f"bytes={existing_size}-")

    try:
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as error:
        if error.code != 416:
            raise
        print(f"range request rejected for {destination}, restarting full download")
        destination.unlink(missing_ok=True)
        existing_size = 0
        response = urllib.request.urlopen(urllib.request.Request(url))

    with response:
        resumable = existing_size and getattr(response, "status", None) == 206
        mode = "ab" if resumable else "wb"
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
    answer_whitelist: list[str],
    answer_blacklist: set[str],
) -> None:
    words: list[str] = []
    vectors: list[list[float]] = []
    seen: set[str] = set()
    answer_words: list[str] = []
    filtered_answer_whitelist = [word for word in answer_whitelist if looks_like_answer_candidate(word)]

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
            if (
                len(answer_words) < max_answer_vocab
                and looks_like_answer_candidate(word)
                and word not in answer_blacklist
            ):
                answer_words.append(word)
            if len(words) >= max_vocab:
                break

    if filtered_answer_whitelist:
        allowed = set(words)
        curated: list[str] = []
        seen_answers: set[str] = set()
        for word in filtered_answer_whitelist:
            if word in allowed and word not in answer_blacklist and word not in seen_answers:
                curated.append(word)
                seen_answers.add(word)
        for word in answer_words:
            if word not in seen_answers:
                curated.append(word)
                seen_answers.add(word)
            if len(curated) >= max_answer_vocab:
                break
        answer_words = curated[:max_answer_vocab]
    else:
        answer_words = [word for word in answer_words if word not in answer_blacklist][:max_answer_vocab]

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
                "guess_pool_strategy": "lexicon-filtered" if noun_lexicon else "broad-hangul-noun-filter",
                "answer_whitelist_applied": bool(filtered_answer_whitelist),
                "answer_blacklist_applied": bool(answer_blacklist),
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
    noun_lexicon_path = resolve_optional_path(args.noun_lexicon)
    answer_whitelist_path = resolve_optional_path(args.answer_whitelist)
    answer_blacklist_path = resolve_optional_path(args.answer_blacklist)
    noun_lexicon = load_noun_lexicon(noun_lexicon_path)
    answer_whitelist = load_word_list(answer_whitelist_path)
    answer_blacklist = set(load_word_list(answer_blacklist_path))
    if noun_lexicon and len(noun_lexicon) < 1000 and not args.allow_small_lexicon:
        raise SystemExit(
            "Refusing to use a tiny noun lexicon for the full guess pool. "
            "Remove --noun-lexicon, or pass --allow-small-lexicon if you intentionally want a tiny allowed vocabulary."
        )
    print(f"downloading official fastText Korean vectors to {cache_path}")
    download_with_resume(args.download_url, cache_path)
    print(f"converting to filtered app dataset in {output_dir}")
    convert_vec_gz(
        cache_path,
        output_dir,
        args.max_vocab,
        noun_lexicon,
        args.max_answer_vocab,
        answer_whitelist,
        answer_blacklist,
    )
    print(f"done: wrote vectors to {output_dir}")


if __name__ == "__main__":
    main()
