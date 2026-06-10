import { useState } from "react";

import { RoomPage } from "./pages/RoomPage";
import { SoloPage } from "./pages/SoloPage";

type Mode = "solo" | "room";

export default function App() {
  const [mode, setMode] = useState<Mode>("solo");
  const [playerName, setPlayerName] = useState("플레이어");
  const columns = ["A", "B", "C", "D", "E", "F", "G", "H"];
  const rowNumbers = Array.from({ length: 24 }, (_, index) => index + 1);

  return (
    <div className="excel-shell">
      <header className="excel-titlebar">
        <div className="excel-brand">
          <div className="excel-badge">X</div>
          <div className="brand-block">
            <p className="eyebrow">Spreadsheet Workspace</p>
            <h1>뉴맨틀 운영 시트</h1>
            <p className="meta-text">
              fastText 한국어 임베딩 기반 추측 게임을 스프레드시트형 대시보드로 운영하는 화면입니다.
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
      <section className="excel-ribbon">
        <div className="excel-toolbar">
          <span className="ribbon-label">시트 보기</span>
          <div className="tabset">
            <button className={mode === "solo" ? "active" : ""} onClick={() => setMode("solo")}>
              오늘의 게임
            </button>
            <button className={mode === "room" ? "active" : ""} onClick={() => setMode("room")}>
              방 경쟁
            </button>
          </div>
        </div>
        <div className="excel-toolbar">
          <span className="ribbon-label">배포 상태</span>
          <p className="meta-text">정적 빌드 시 FastAPI가 현재 시트를 그대로 서빙합니다.</p>
        </div>
      </section>
      <section className="formula-bar">
        <div className="name-box">{mode === "solo" ? "B2" : "D4"}</div>
        <div className="formula-label">fx</div>
        <div className="formula-input">
          ="{mode === "solo" ? "오늘의 게임 진행 현황" : "방 경쟁 진행 현황"} / 사용자: {playerName}"
        </div>
      </section>
      <main className="sheet-stage">
        <div className="sheet-frame">
          <div className="sheet-corner" />
          <div className="column-headers">
            {columns.map((column) => (
              <span key={column}>{column}</span>
            ))}
          </div>
          <div className="row-headers">
            {rowNumbers.map((row) => (
              <span key={row}>{row}</span>
            ))}
          </div>
          <div className="sheet-body">
            <div className="sheet-surface">
              <div className="content">
                {mode === "solo" ? <SoloPage playerName={playerName} /> : <RoomPage playerName={playerName} />}
              </div>
            </div>
          </div>
        </div>
        <div className="sheet-tabs">
          <button className={`sheet-tab ${mode === "solo" ? "active" : ""}`} onClick={() => setMode("solo")}>
            Daily
          </button>
          <button className={`sheet-tab ${mode === "room" ? "active" : ""}`} onClick={() => setMode("room")}>
            Rooms
          </button>
        </div>
      </main>
    </div>
  );
}
