import { FormEvent, useEffect, useState } from "react";

import { RoomBoard } from "../components/RoomBoard";
import { api, roomWebSocketUrl, type RoomState } from "../lib/api";

type Props = {
  playerName: string;
};

export function RoomPage({ playerName }: Props) {
  const [roomIdInput, setRoomIdInput] = useState("");
  const [roomId, setRoomId] = useState<string | null>(null);
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [room, setRoom] = useState<RoomState | null>(null);
  const [word, setWord] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!roomId) {
      return;
    }

    let cancelled = false;
    let socket: WebSocket | null = null;
    const load = async () => {
      try {
        const next = await api.getRoom(roomId);
        if (!cancelled) {
          setRoom(next);
        }
      } catch (reason) {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "room fetch failed");
        }
      }
    };

    void load();
    socket = new WebSocket(roomWebSocketUrl(roomId));
    socket.onmessage = (event) => {
      if (cancelled) {
        return;
      }
      const next = JSON.parse(event.data) as RoomState;
      setRoom(next);
    };
    const timer = window.setInterval(() => {
      socket?.readyState === WebSocket.OPEN ? socket.send("ping") : void load();
    }, 3000);
    return () => {
      cancelled = true;
      socket?.close();
      window.clearInterval(timer);
    };
  }, [roomId]);

  async function createRoom() {
    setError(null);
    const created = await api.createRoom(playerName);
    setRoomId(created.room_id);
    setPlayerId(created.player_id);
    setRoomIdInput(created.room_id);
  }

  async function joinRoom(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      const joined = await api.joinRoom(roomIdInput.toUpperCase(), playerName);
      setRoomId(joined.room_id);
      setPlayerId(joined.player_id);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "join failed");
    }
  }

  async function submitGuess(event: FormEvent) {
    event.preventDefault();
    if (!roomId || !playerId) {
      return;
    }
    setError(null);
    try {
      await api.submitRoomGuess(roomId, playerId, word);
      setWord("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "room guess failed");
    }
  }

  return (
    <section className="stack">
      <div className="hero-card accent-card hero-card-room">
        <div className="hero-topline">
          <div>
            <p className="eyebrow">Room Match</p>
            <h2>방마다 별도 정답으로 경쟁</h2>
          </div>
          <div className="stat-strip">
            <div className="stat-chip">
              <span>이름</span>
              <strong>{playerName}</strong>
            </div>
            <div className="stat-chip">
              <span>현재 방</span>
              <strong>{roomId ?? "-"}</strong>
            </div>
            <div className="stat-chip">
              <span>참가자</span>
              <strong>{room?.members.length ?? 0}</strong>
            </div>
          </div>
        </div>
        <p className="hero-copy">
          모두가 같은 정답을 풀지만, 보이는 것은 누가 얼마나 가까워졌는지에 대한 상태와 순위입니다.
        </p>
        <div className="room-actions">
          <button type="button" onClick={createRoom}>
            방 만들기
          </button>
          <form className="inline-form" onSubmit={joinRoom}>
            <input
              value={roomIdInput}
              onChange={(event) => setRoomIdInput(event.target.value)}
              placeholder="방 코드"
            />
            <button type="submit">입장</button>
          </form>
        </div>
        {roomId ? <p className="meta-text">방 코드 `{roomId}` 를 공유해서 다른 사람을 입장시키면 됩니다.</p> : null}
        {roomId && playerId ? (
          <form className="guess-form" onSubmit={submitGuess}>
            <input value={word} onChange={(event) => setWord(event.target.value)} placeholder="이 방의 정답 단어 추측" />
            <button type="submit">추측</button>
          </form>
        ) : null}
        {error ? <p className="error-text">{error}</p> : null}
      </div>
      {room ? <RoomBoard room={room} /> : null}
    </section>
  );
}
