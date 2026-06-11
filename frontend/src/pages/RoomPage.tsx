import { FormEvent, useEffect, useState } from "react";

import { RoomBoard } from "../components/RoomBoard";
import { api, roomWebSocketUrl, type RoomState } from "../lib/api";

type Props = {
  playerName: string;
  adminPassword: string | null;
};

export function RoomPage({ playerName, adminPassword }: Props) {
  const [roomIdInput, setRoomIdInput] = useState("");
  const [roomId, setRoomId] = useState<string | null>(null);
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [room, setRoom] = useState<RoomState | null>(null);
  const [word, setWord] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adminReveal, setAdminReveal] = useState<{ word: string; answer_length: number; tags: string[]; description: string } | null>(null);
  const normalizedRoomIdInput = roomIdInput.toUpperCase();
  const alreadyJoinedCurrentRoom = Boolean(roomId && playerId && normalizedRoomIdInput === roomId);

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

  useEffect(() => {
    if (!adminPassword || !roomId) {
      setAdminReveal(null);
      return;
    }
    api.getAdminRoomAnswer(roomId, adminPassword).then(setAdminReveal).catch(() => setAdminReveal(null));
  }, [adminPassword, roomId]);

  async function createRoom() {
    setError(null);
    const created = await api.createRoom(playerName);
    setRoomId(created.room_id);
    setPlayerId(created.player_id);
    setRoomIdInput(created.room_id);
  }

  async function joinRoom(event: FormEvent) {
    event.preventDefault();
    if (alreadyJoinedCurrentRoom) {
      return;
    }
    setError(null);
    try {
      const joined = await api.joinRoom(normalizedRoomIdInput, playerName);
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
    <section className="worksheet-grid worksheet-grid-room">
      <section className="worksheet-region worksheet-room-title">
        <div className="worksheet-region-head">
          <div>
            <p className="eyebrow">Room Match</p>
            <h2>방마다 별도 정답으로 경쟁</h2>
          </div>
        </div>
        <p className="hero-copy">보이는 것은 누가 얼마나 가까워졌는지에 대한 상태와 순위입니다.</p>
      </section>

      <section className="worksheet-region worksheet-room-summary">
        <div className="worksheet-key-table">
          <div><span>이름</span><strong>{playerName}</strong></div>
          <div><span>현재 방</span><strong>{roomId ?? "-"}</strong></div>
          <div><span>참가자</span><strong>{room?.members.length ?? 0}</strong></div>
          <div><span>접속 상태</span><strong>{playerId ? "참가 중" : "대기"}</strong></div>
        </div>
      </section>

      <section className="worksheet-region worksheet-room-join">
        <div className="room-actions">
          <button type="button" onClick={createRoom}>
            방 만들기
          </button>
          <form className="inline-form" onSubmit={joinRoom}>
            <input
              value={roomIdInput}
              onChange={(event) => setRoomIdInput(event.target.value.toUpperCase())}
              placeholder="방 코드"
            />
            <button type="submit" disabled={alreadyJoinedCurrentRoom}>
              {alreadyJoinedCurrentRoom ? "입장됨" : "입장"}
            </button>
          </form>
        </div>
      </section>

      <section className="worksheet-region worksheet-room-meta">
        {roomId ? <p className="meta-text">방 코드 `{roomId}` 를 공유해서 다른 사람을 입장시키면 됩니다.</p> : null}
        {room ? (
          <p className="meta-text">
            순위는 1000위 미만만 숫자로 표시합니다. 상위 1000위 단어는 고정 유지되고, 1000위 이상은 유사도순으로 정리됩니다.
          </p>
        ) : null}
        {roomId && playerId ? (
          <form className="guess-form" onSubmit={submitGuess}>
            <input value={word} onChange={(event) => setWord(event.target.value)} placeholder="이 방의 정답 단어 추측" />
            <button type="submit">추측</button>
          </form>
        ) : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      {adminReveal ? (
        <section className="worksheet-region worksheet-admin">
          <div className="worksheet-region-head">
            <h3>관리자 메뉴</h3>
            <span>방 정답 보기</span>
          </div>
          <div className="worksheet-key-table worksheet-key-table-compact">
            <div><span>정답</span><strong>{adminReveal.word}</strong></div>
            <div><span>길이</span><strong>{adminReveal.answer_length}</strong></div>
            <div><span>태그</span><strong>{adminReveal.tags.join(", ")}</strong></div>
          </div>
          <p className="meta-text">{adminReveal.description}</p>
        </section>
      ) : null}

      {room ? <RoomBoard room={room} currentPlayerId={playerId} /> : null}
    </section>
  );
}
