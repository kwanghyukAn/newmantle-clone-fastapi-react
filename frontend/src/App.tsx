import { useState } from "react";

import { RoomPage } from "./pages/RoomPage";
import { SoloPage } from "./pages/SoloPage";

type Mode = "solo" | "room";

export default function App() {
  const [mode, setMode] = useState<Mode>("solo");
  const [playerName, setPlayerName] = useState("플레이어");

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <p className="eyebrow">Internal Word Similarity Game</p>
          <h1>뉴맨틀 클론</h1>
          <p className="meta-text">
            공식 fastText 한국어 임베딩을 기준으로 운영 가능한 구조로 정리한 FastAPI + React 워크스페이스입니다.
          </p>
        </div>
        <div className="topbar-controls">
          <input value={playerName} onChange={(event) => setPlayerName(event.target.value)} placeholder="이름" />
          <div className="tabset">
            <button className={mode === "solo" ? "active" : ""} onClick={() => setMode("solo")}>
              오늘의 게임
            </button>
            <button className={mode === "room" ? "active" : ""} onClick={() => setMode("room")}>
              방 경쟁
            </button>
          </div>
        </div>
      </header>
      <main className="content">
        {mode === "solo" ? <SoloPage playerName={playerName} /> : <RoomPage playerName={playerName} />}
      </main>
    </div>
  );
}
