import { useState } from "react";

import { RoomPage } from "./pages/RoomPage";
import { SoloPage } from "./pages/SoloPage";

type Mode = "solo" | "room";

export default function App() {
  const [mode, setMode] = useState<Mode>("solo");
  const [playerName, setPlayerName] = useState("플레이어");

  return (
    <div className="office-shell">
      <header className="office-bar">
        <div className="office-brand">
          <div className="office-badge">W</div>
          <div className="brand-block">
            <p className="eyebrow">Word Similarity Workspace</p>
            <h1>뉴맨틀 업무형 보드</h1>
            <p className="meta-text">
              fastText 한국어 임베딩 기반 추측 게임을 단일 서버에서 운영할 수 있게 정리한 배포형 워크스페이스입니다.
            </p>
          </div>
        </div>
        <div className="topbar-controls">
          <label className="field-stack">
            <span>참가자 이름</span>
            <input value={playerName} onChange={(event) => setPlayerName(event.target.value)} placeholder="이름" />
          </label>
        </div>
      </header>
      <section className="ribbon">
        <div className="ribbon-group">
          <span className="ribbon-label">게임 모드</span>
          <div className="tabset">
            <button className={mode === "solo" ? "active" : ""} onClick={() => setMode("solo")}>
              오늘의 게임
            </button>
            <button className={mode === "room" ? "active" : ""} onClick={() => setMode("room")}>
              방 경쟁
            </button>
          </div>
        </div>
        <div className="ribbon-group ribbon-note">
          <span className="ribbon-label">배포 모드</span>
          <p className="meta-text">정적 빌드 후 FastAPI가 `/`와 `/assets`를 직접 서빙합니다.</p>
        </div>
      </section>
      <main className="document-stage">
        <div className="document-page">
          <div className="content">
            {mode === "solo" ? <SoloPage playerName={playerName} /> : <RoomPage playerName={playerName} />}
          </div>
        </div>
      </main>
    </div>
  );
}
