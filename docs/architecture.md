# Architecture Notes

## Product Decisions

- Vocabulary: Korean common nouns only.
- Multiplayer: each room gets its own answer word.
- Similarity engine: local embedding vectors with cosine similarity.

## Backend Shape

- `app/services/embedding_store.py`
  - Loads either:
    - compressed `npz` fastText-derived vectors plus a word list, or
    - the tiny seed JSON fallback.
  - The production path is optimized for a filtered `float32` matrix instead of a huge JSON blob.

- `app/services/game_engine.py`
  - Owns normalization, cosine similarity, ranking, daily answer selection, room answer selection, and hint generation.
  - This is the layer to keep stable while swapping the vector source.

- `app/services/room_service.py`
  - Tracks room membership, attempts, best rank, best similarity, and recent guesses.
  - Uses a SQLite repository for persistence.

- `app/services/storage.py`
  - Stores daily guesses, rooms, players, and room guesses in SQLite.
  - This keeps the prototype durable across server restarts without introducing a larger ORM yet.

- `app/services/realtime.py`
  - Maintains WebSocket subscriptions per room and broadcasts room-state snapshots.

## Frontend Shape

- `SoloPage`
  - Daily single-player guessing loop.
- `RoomPage`
  - Room create/join flow.
  - Shared progress board and recent-guess feed.
  - Uses WebSocket room updates, with polling fallback if the socket is unavailable.

## Immediate Next Steps

1. Run the included fastText preparation command on the target machine.
2. Add a Korean noun lexicon intersection step for cleaner answer/guess pools.
3. Implement hint/give-up/share parity with the reference game.
4. Move from SQLite to PostgreSQL when multi-instance deployment becomes necessary.
