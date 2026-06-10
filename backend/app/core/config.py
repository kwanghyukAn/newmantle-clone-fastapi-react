from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
FULL_WORDS_PATH = BASE_DIR / "app" / "data" / "fasttext_ko_words.json"
FULL_VECTORS_PATH = BASE_DIR / "app" / "data" / "fasttext_ko_vectors.npz"
FULL_METADATA_PATH = BASE_DIR / "app" / "data" / "fasttext_ko_metadata.json"
FULL_ANSWER_WORDS_PATH = BASE_DIR / "app" / "data" / "fasttext_ko_answer_words.json"
DATA_PATH = BASE_DIR / "app" / "data" / "korean_nouns_seed.json"
DB_PATH = BASE_DIR / "newmantle.sqlite3"
