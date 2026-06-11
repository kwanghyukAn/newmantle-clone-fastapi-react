from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator

from app.models.schemas import GuessResult, RevealResult, RoomGuessView, RoomMemberView, RoomSolveLeader


class SQLiteRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS daily_guesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    word TEXT NOT NULL,
                    similarity REAL NOT NULL,
                    rank_value INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    attempt INTEGER NOT NULL,
                    UNIQUE(player_name, game_date, attempt)
                );

                CREATE TABLE IF NOT EXISTS daily_sessions (
                    player_name TEXT NOT NULL,
                    game_date TEXT NOT NULL,
                    hint_count INTEGER NOT NULL DEFAULT 0,
                    initial_hint_used INTEGER NOT NULL DEFAULT 0,
                    revealed INTEGER NOT NULL DEFAULT 0,
                    reveal_word TEXT,
                    reveal_tags TEXT,
                    reveal_description TEXT,
                    PRIMARY KEY(player_name, game_date)
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    answer_word TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS room_players (
                    player_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    solved INTEGER NOT NULL DEFAULT 0,
                    solve_order INTEGER,
                    solved_at TEXT,
                    last_active_at TEXT NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id)
                );

                CREATE TABLE IF NOT EXISTS room_guesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    word TEXT NOT NULL,
                    similarity REAL NOT NULL,
                    rank_value INTEGER NOT NULL,
                    correct INTEGER NOT NULL,
                    attempt INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(room_id) REFERENCES rooms(room_id),
                    FOREIGN KEY(player_id) REFERENCES room_players(player_id)
                );
                """
            )
            room_player_columns = {
                str(row["name"]) for row in conn.execute("PRAGMA table_info(room_players)").fetchall()
            }
            if "solve_order" not in room_player_columns:
                conn.execute("ALTER TABLE room_players ADD COLUMN solve_order INTEGER")
            if "solved_at" not in room_player_columns:
                conn.execute("ALTER TABLE room_players ADD COLUMN solved_at TEXT")

    def get_daily_guesses(self, player_name: str | None, game_date: date) -> list[GuessResult]:
        key = player_name or "anonymous"
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT word, similarity, rank_value, correct, attempt
                FROM daily_guesses
                WHERE player_name = ? AND game_date = ?
                ORDER BY attempt ASC
                """,
                (key, game_date.isoformat()),
            ).fetchall()
        return [self._guess_from_row(row) for row in rows]

    def get_daily_session_meta(self, player_name: str | None, game_date: date) -> dict[str, object]:
        key = player_name or "anonymous"
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT hint_count, initial_hint_used, revealed, reveal_word, reveal_tags, reveal_description
                FROM daily_sessions
                WHERE player_name = ? AND game_date = ?
                """,
                (key, game_date.isoformat()),
            ).fetchone()
        if row is None:
            return {
                "hint_count": 0,
                "initial_hint_used": False,
                "revealed": False,
                "reveal": None,
            }
        reveal = None
        if row["revealed"] and row["reveal_word"]:
            reveal = RevealResult(
                word=str(row["reveal_word"]),
                answer_length=len(str(row["reveal_word"])),
                tags=json_load_list(str(row["reveal_tags"]) if row["reveal_tags"] else "[]"),
                description=str(row["reveal_description"] or ""),
            )
        return {
            "hint_count": int(row["hint_count"]),
            "initial_hint_used": bool(row["initial_hint_used"]),
            "revealed": bool(row["revealed"]),
            "reveal": reveal,
        }

    def save_daily_guess(self, player_name: str | None, game_date: date, guess: GuessResult) -> None:
        key = player_name or "anonymous"
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_sessions (player_name, game_date)
                VALUES (?, ?)
                ON CONFLICT(player_name, game_date) DO NOTHING
                """,
                (key, game_date.isoformat()),
            )
            conn.execute(
                """
                INSERT INTO daily_guesses (player_name, game_date, word, similarity, rank_value, correct, attempt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    game_date.isoformat(),
                    guess.word,
                    guess.similarity,
                    guess.rank,
                    int(guess.correct),
                    guess.attempt,
                ),
            )

    def increment_daily_hint(self, player_name: str | None, game_date: date) -> None:
        key = player_name or "anonymous"
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_sessions (player_name, game_date, hint_count)
                VALUES (?, ?, 1)
                ON CONFLICT(player_name, game_date)
                DO UPDATE SET hint_count = hint_count + 1
                """,
                (key, game_date.isoformat()),
            )

    def mark_daily_initial_hint(self, player_name: str | None, game_date: date) -> None:
        key = player_name or "anonymous"
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_sessions (player_name, game_date, initial_hint_used)
                VALUES (?, ?, 1)
                ON CONFLICT(player_name, game_date)
                DO UPDATE SET initial_hint_used = 1
                """,
                (key, game_date.isoformat()),
            )

    def reveal_daily_answer(
        self,
        player_name: str | None,
        game_date: date,
        reveal: RevealResult,
    ) -> None:
        key = player_name or "anonymous"
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO daily_sessions (
                    player_name, game_date, revealed, reveal_word, reveal_tags, reveal_description
                ) VALUES (?, ?, 1, ?, ?, ?)
                ON CONFLICT(player_name, game_date)
                DO UPDATE SET
                    revealed = 1,
                    reveal_word = excluded.reveal_word,
                    reveal_tags = excluded.reveal_tags,
                    reveal_description = excluded.reveal_description
                """,
                (
                    key,
                    game_date.isoformat(),
                    reveal.word,
                    json_dump_list(reveal.tags),
                    reveal.description,
                ),
            )

    def create_room(self, room_id: str, answer_word: str, created_at: datetime, player_id: str, host_name: str) -> None:
        timestamp = created_at.astimezone(timezone.utc).isoformat()
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO rooms (room_id, answer_word, created_at) VALUES (?, ?, ?)",
                (room_id, answer_word, timestamp),
            )
            conn.execute(
                """
                INSERT INTO room_players (player_id, room_id, name, solved, solve_order, solved_at, last_active_at)
                VALUES (?, ?, ?, 0, NULL, NULL, ?)
                """,
                (player_id, room_id, host_name, timestamp),
            )

    def add_room_player(self, room_id: str, player_id: str, name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO room_players (player_id, room_id, name, solved, solve_order, solved_at, last_active_at)
                VALUES (?, ?, ?, 0, NULL, NULL, ?)
                """,
                (player_id, room_id, name, now),
            )

    def find_room_player_id_by_name(self, room_id: str, name: str) -> str | None:
        normalized = name.strip()
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT player_id
                FROM room_players
                WHERE room_id = ? AND TRIM(name) = ?
                ORDER BY last_active_at DESC
                LIMIT 1
                """,
                (room_id, normalized),
            ).fetchone()
        return None if row is None else str(row["player_id"])

    def touch_room_player(self, player_id: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE room_players
                SET last_active_at = ?
                WHERE player_id = ?
                """,
                (datetime.now(timezone.utc).isoformat(), player_id),
            )

    def room_exists(self, room_id: str) -> bool:
        with self.connection() as conn:
            row = conn.execute("SELECT 1 FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
        return row is not None

    def get_room_answer_word(self, room_id: str) -> str | None:
        with self.connection() as conn:
            row = conn.execute("SELECT answer_word FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
        return None if row is None else str(row["answer_word"])

    def get_room_created_at(self, room_id: str) -> datetime | None:
        with self.connection() as conn:
            row = conn.execute("SELECT created_at FROM rooms WHERE room_id = ?", (room_id,)).fetchone()
        return None if row is None else datetime.fromisoformat(str(row["created_at"]))

    def room_player_exists(self, room_id: str, player_id: str) -> bool:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM room_players WHERE room_id = ? AND player_id = ?",
                (room_id, player_id),
            ).fetchone()
        return row is not None

    def get_player_attempt_count(self, room_id: str, player_id: str) -> int:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM room_guesses WHERE room_id = ? AND player_id = ?",
                (room_id, player_id),
            ).fetchone()
        return int(row["count"])

    def get_player_name(self, player_id: str) -> str | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT name FROM room_players WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        return None if row is None else str(row["name"])

    def save_room_guess(self, room_id: str, player_id: str, player_name: str, guess: GuessResult) -> datetime:
        created_at = datetime.now(timezone.utc)
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO room_guesses (
                    room_id, player_id, name, word, similarity, rank_value, correct, attempt, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    room_id,
                    player_id,
                    player_name,
                    guess.word,
                    guess.similarity,
                    guess.rank,
                    int(guess.correct),
                    guess.attempt,
                    created_at.isoformat(),
                ),
            )
            conn.execute(
                """
                UPDATE room_players
                SET solved = CASE WHEN ? = 1 THEN 1 ELSE solved END,
                    solve_order = CASE
                        WHEN ? = 1 AND solved = 0 THEN COALESCE(
                            (SELECT MAX(solve_order) FROM room_players WHERE room_id = ?),
                            0
                        ) + 1
                        ELSE solve_order
                    END,
                    solved_at = CASE
                        WHEN ? = 1 AND solved = 0 THEN ?
                        ELSE solved_at
                    END,
                    last_active_at = ?
                WHERE player_id = ?
                """,
                (
                    int(guess.correct),
                    int(guess.correct),
                    room_id,
                    int(guess.correct),
                    created_at.isoformat(),
                    created_at.isoformat(),
                    player_id,
                ),
            )
        return created_at

    def list_room_members(self, room_id: str) -> list[RoomMemberView]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    p.player_id,
                    p.name,
                    p.solved,
                    p.solve_order,
                    p.solved_at,
                    p.last_active_at,
                    COUNT(g.id) AS attempts,
                    MIN(g.rank_value) AS best_rank,
                    MAX(g.similarity) AS best_similarity
                FROM room_players p
                LEFT JOIN room_guesses g
                  ON p.player_id = g.player_id AND p.room_id = g.room_id
                WHERE p.room_id = ?
                GROUP BY p.player_id, p.name, p.solved, p.solve_order, p.solved_at, p.last_active_at
                ORDER BY
                    p.solved DESC,
                    CASE WHEN p.solve_order IS NULL THEN 999999 ELSE p.solve_order END ASC,
                    CASE WHEN MIN(g.rank_value) IS NULL THEN 999999 ELSE MIN(g.rank_value) END ASC,
                    MAX(g.similarity) DESC,
                    COUNT(g.id) ASC,
                    p.name ASC
                """,
                (room_id,),
            ).fetchall()

        return [
            RoomMemberView(
                player_id=str(row["player_id"]),
                name=str(row["name"]),
                attempts=int(row["attempts"]),
                best_rank=None if row["best_rank"] is None else int(row["best_rank"]),
                best_similarity=None if row["best_similarity"] is None else float(row["best_similarity"]),
                solved=bool(row["solved"]),
                solve_order=None if row["solve_order"] is None else int(row["solve_order"]),
                solved_at=None if row["solved_at"] is None else datetime.fromisoformat(str(row["solved_at"])),
                last_active_at=datetime.fromisoformat(str(row["last_active_at"])),
            )
            for row in rows
        ]

    def get_room_first_solver(self, room_id: str) -> RoomSolveLeader | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT player_id, name, solve_order, solved_at
                FROM room_players
                WHERE room_id = ? AND solve_order IS NOT NULL
                ORDER BY solve_order ASC
                LIMIT 1
                """,
                (room_id,),
            ).fetchone()
        if row is None:
            return None
        return RoomSolveLeader(
            player_id=str(row["player_id"]),
            name=str(row["name"]),
            solve_order=int(row["solve_order"]),
            solved_at=datetime.fromisoformat(str(row["solved_at"])),
        )

    def list_recent_room_guesses(self, room_id: str, limit: int = 20) -> list[RoomGuessView]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT player_id, name, word, similarity, rank_value, correct, attempt, created_at
                FROM room_guesses
                WHERE room_id = ?
                ORDER BY id DESC
                """,
                (room_id,),
            ).fetchall()

        unique_rows: dict[str, sqlite3.Row] = {}
        for row in rows:
            normalized = self._normalize_hint_word(str(row["word"]))
            current = unique_rows.get(normalized)
            if current is None or self._is_better_hint_row(row, current):
                unique_rows[normalized] = row

        pinned_rows = [
            row
            for row in unique_rows.values()
            if bool(row["correct"]) or int(row["rank_value"]) < 1000
        ]
        overflow_rows = [
            row
            for row in unique_rows.values()
            if not bool(row["correct"]) and int(row["rank_value"]) >= 1000
        ]
        pinned_rows.sort(key=self._hint_sort_key)
        overflow_rows.sort(key=lambda row: (-float(row["similarity"]), int(row["rank_value"]), str(row["created_at"])))

        ordered_rows = pinned_rows + overflow_rows[:limit]
        return [
            RoomGuessView(
                player_id=str(row["player_id"]),
                name=str(row["name"]),
                word=str(row["word"]),
                similarity=float(row["similarity"]),
                rank=int(row["rank_value"]),
                correct=bool(row["correct"]),
                attempt=int(row["attempt"]),
                created_at=datetime.fromisoformat(str(row["created_at"])),
            )
            for row in ordered_rows
        ]

    @staticmethod
    def _normalize_hint_word(word: str) -> str:
        return word.strip().lower().replace(" ", "")

    @staticmethod
    def _is_better_hint_row(candidate: sqlite3.Row, current: sqlite3.Row) -> bool:
        candidate_correct = bool(candidate["correct"])
        current_correct = bool(current["correct"])
        if candidate_correct != current_correct:
            return candidate_correct
        candidate_rank = int(candidate["rank_value"])
        current_rank = int(current["rank_value"])
        if candidate_rank != current_rank:
            return candidate_rank < current_rank
        candidate_similarity = float(candidate["similarity"])
        current_similarity = float(current["similarity"])
        if candidate_similarity != current_similarity:
            return candidate_similarity > current_similarity
        return str(candidate["created_at"]) > str(current["created_at"])

    @staticmethod
    def _hint_sort_key(row: sqlite3.Row) -> tuple[int, float, str]:
        rank = int(row["rank_value"])
        return (rank, -float(row["similarity"]), str(row["created_at"]))

    @staticmethod
    def _guess_from_row(row: sqlite3.Row) -> GuessResult:
        return GuessResult(
            word=str(row["word"]),
            similarity=float(row["similarity"]),
            rank=int(row["rank_value"]),
            correct=bool(row["correct"]),
            attempt=int(row["attempt"]),
        )


def json_dump_list(values: list[str]) -> str:
    import json

    return json.dumps(values, ensure_ascii=False)


def json_load_list(raw: str) -> list[str]:
    import json

    loaded = json.loads(raw)
    return [str(value) for value in loaded]
