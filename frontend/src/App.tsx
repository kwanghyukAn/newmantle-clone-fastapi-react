import { FormEvent, useEffect, useState } from "react";

import { RoomPage } from "./pages/RoomPage";
import { SoloPage } from "./pages/SoloPage";
import { api } from "./lib/api";

type Mode = "solo" | "room";

export default function App() {
  const [mode, setMode] = useState<Mode>("solo");
  const [playerName, setPlayerName] = useState("플레이어");
  const [zoom, setZoom] = useState(100);
  const [, setAdminClickCount] = useState(0);
  const [adminPromptOpen, setAdminPromptOpen] = useState(false);
  const [adminInput, setAdminInput] = useState("");
  const [adminPassword, setAdminPassword] = useState<string | null>(null);
  const [adminError, setAdminError] = useState<string | null>(null);
  const [adminStatus, setAdminStatus] = useState<string | null>(null);
  const columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"];
  const rowNumbers = Array.from({ length: 34 }, (_, index) => index + 1);
  const activeCell = mode === "solo" ? "B2" : "D4";

  function handleConditionalFormattingClick() {
    setAdminClickCount((current) => {
      const next = current + 1;
      if (next >= 5) {
        setAdminError(null);
        setAdminPromptOpen(true);
        return 0;
      }
      return next;
    });
  }

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (event.altKey && event.shiftKey && event.key.toLowerCase() === "a") {
        event.preventDefault();
        setAdminError(null);
        setAdminPromptOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, []);

  async function handleAdminSubmit(event: FormEvent) {
    event.preventDefault();
    setAdminError(null);
    try {
      const result = await api.verifyAdmin(adminInput.trim());
      if (result.unlocked) {
        setAdminPassword(adminInput.trim());
        setAdminStatus("관리자 모드가 활성화되었습니다.");
        setAdminPromptOpen(false);
        setAdminInput("");
        setAdminClickCount(0);
      }
    } catch (reason) {
      setAdminError(reason instanceof Error ? reason.message : "admin verification failed");
    }
  }

  return (
    <div className="excel-shell">
      <header className="excel-windowbar">
        <div className="windowbar-left">
          <div className="excel-badge">X</div>
          <div className="quick-actions">
            <button type="button" aria-label="save">
              저장
            </button>
            <button type="button" aria-label="undo">
              실행취소
            </button>
            <button type="button" aria-label="redo">
              다시실행
            </button>
          </div>
        </div>
        <div className="windowbar-title">cap_prune - Excel</div>
        <div className="windowbar-right">
          <label className="windowbar-search">
            <span aria-hidden="true">🔍</span>
            <input type="text" value="검색" readOnly />
          </label>
          <button type="button" className="windowbar-share">
            공유 ▼
          </button>
          <div className="window-controls" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </div>
      </header>
      <section className="excel-ribbon-shell">
        <div className="excel-tabbar">
          <button type="button" className="excel-tab file-tab">
            파일
          </button>
          <button type="button" className="excel-tab active">
            홈
          </button>
          <button type="button" className="excel-tab">
            삽입
          </button>
          <button type="button" className="excel-tab">
            페이지 레이아웃
          </button>
          <button type="button" className="excel-tab">
            수식
          </button>
          <button type="button" className="excel-tab">
            데이터
          </button>
          <button type="button" className="excel-tab">
            검토
          </button>
          <button type="button" className="excel-tab">
            보기
          </button>
        </div>
        <div className="excel-ribbon">
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool is-strong">
                <span className="ribbon-tool-icon ribbon-tool-icon-paste" aria-hidden="true" />
                붙여넣기
              </button>
              <div className="ribbon-mini-stack">
                <button type="button" className="ribbon-tool-mini">
                  <span className="ribbon-tool-icon ribbon-tool-icon-cut" aria-hidden="true" />
                </button>
                <button type="button" className="ribbon-tool-mini">
                  <span className="ribbon-tool-icon ribbon-tool-icon-copy" aria-hidden="true" />
                </button>
              </div>
            </div>
            <span className="ribbon-group-label">클립보드</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-combo-row">
              <div className="ribbon-combo">맑은 고딕</div>
              <div className="ribbon-combo ribbon-combo-size">11</div>
            </div>
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-bold" aria-hidden="true" />
                굵게
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-italic" aria-hidden="true" />
                기울임
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-underline" aria-hidden="true" />
                밑줄
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-border" aria-hidden="true" />
                테두리
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-fill" aria-hidden="true" />
                채우기
              </button>
            </div>
            <span className="ribbon-group-label">글꼴</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-align-left" aria-hidden="true" />
                왼쪽
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-align-center" aria-hidden="true" />
                가운데
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-align-right" aria-hidden="true" />
                오른쪽
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-merge" aria-hidden="true" />
                병합
              </button>
            </div>
            <span className="ribbon-group-label">맞춤</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-combo-row">
              <div className="ribbon-combo">일반</div>
            </div>
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool narrow">
                %
              </button>
              <button type="button" className="ribbon-tool narrow">
                ,
              </button>
              <button type="button" className="ribbon-tool narrow">
                .0
              </button>
              <button type="button" className="ribbon-tool narrow">
                .00
              </button>
            </div>
            <span className="ribbon-group-label">표시 형식</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="tabset">
              <button type="button" className={mode === "solo" ? "active" : ""} onClick={() => setMode("solo")}>
                오늘의 게임
              </button>
              <button type="button" className={mode === "room" ? "active" : ""} onClick={() => setMode("room")}>
                방 경쟁
              </button>
            </div>
            <span className="ribbon-group-label">모드</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool" onClick={handleConditionalFormattingClick} title="관리자 진입: 5회 클릭 또는 Alt+Shift+A">
                <span className="ribbon-tool-icon ribbon-tool-icon-style-block" aria-hidden="true" />
                조건부 서식
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-style-grid" aria-hidden="true" />
                표 서식
              </button>
              <button type="button" className="ribbon-tool">
                <span className="ribbon-tool-icon ribbon-tool-icon-style-cell" aria-hidden="true" />
                셀 스타일
              </button>
            </div>
            <span className="ribbon-group-label">스타일</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool narrow">
                삽입
              </button>
              <button type="button" className="ribbon-tool narrow">
                삭제
              </button>
              <button type="button" className="ribbon-tool narrow">
                서식
              </button>
            </div>
            <span className="ribbon-group-label">셀</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <label className="ribbon-field">
              <span>참가자 이름</span>
              <input value={playerName} onChange={(event) => setPlayerName(event.target.value)} placeholder="이름" />
            </label>
            <span className="ribbon-group-label">세션</span>
          </div>
          <div className="ribbon-group ribbon-group-stack">
            <div className="ribbon-button-row">
              <button type="button" className="ribbon-tool narrow">
                Σ
              </button>
              <button type="button" className="ribbon-tool narrow">
                채우기
              </button>
              <button type="button" className="ribbon-tool narrow">
                지우기
              </button>
              <button type="button" className="ribbon-tool narrow">
                필터
              </button>
              <button type="button" className="ribbon-tool narrow">
                찾기
              </button>
            </div>
            <span className="ribbon-group-label">편집</span>
          </div>
          <div className="ribbon-group ribbon-group-stack ribbon-group-fill">
            <div className="ribbon-status">
              <span className="ribbon-status-title">cap_prune workspace</span>
              <span className="ribbon-status-text">정적 배포, 방 경쟁, 실시간 랭킹, 한국어 의미 유사도 게임</span>
            </div>
            <span className="ribbon-group-label">정보</span>
          </div>
          <div className="ribbon-group ribbon-group-stack ribbon-group-apps">
            <button type="button" className="ribbon-apps-button" aria-label="apps">
              <span className="ribbon-tool-icon ribbon-tool-icon-apps" aria-hidden="true" />
            </button>
            <span className="ribbon-group-label">추가 기능</span>
          </div>
        </div>
      </section>
      <section className="formula-bar">
        <div className="name-box">{activeCell}</div>
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
              <div className={`active-cell-overlay ${mode === "solo" ? "cell-b2" : "cell-d4"}`} aria-hidden="true" />
              <div className="content">
                {mode === "solo" ? (
                  <SoloPage playerName={playerName} adminPassword={adminPassword} />
                ) : (
                  <RoomPage playerName={playerName} adminPassword={adminPassword} />
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="sheet-bottom-chrome">
          <div className="sheet-nav">
            <button type="button" className="sheet-nav-button" aria-label="prev sheet">
              ‹
            </button>
            <button type="button" className="sheet-nav-button" aria-label="next sheet">
              ›
            </button>
          </div>
          <div className="sheet-tabs">
            <button type="button" className={`sheet-tab ${mode === "solo" ? "active" : ""}`} onClick={() => setMode("solo")}>
              Daily
            </button>
            <button type="button" className={`sheet-tab ${mode === "room" ? "active" : ""}`} onClick={() => setMode("room")}>
              Rooms
            </button>
          </div>
          <div className="sheet-scroll-track" aria-hidden="true">
            <div className="sheet-scroll-thumb" />
          </div>
        </div>
      </main>
      <footer className="excel-statusbar">
        <div className="statusbar-left">
          <span className="status-pill">준비</span>
          <span className="status-text">cap_prune</span>
          <span className="status-text">{mode === "solo" ? "오늘의 게임" : "방 경쟁"}</span>
          {adminStatus ? <span className="status-text">{adminStatus}</span> : null}
        </div>
        <div className="statusbar-right">
          <div className="view-controls" aria-hidden="true">
            <span className="view-button active" />
            <span className="view-button" />
            <span className="view-button" />
          </div>
          <div className="zoom-control">
            <span>{zoom}%</span>
            <input
              type="range"
              min="60"
              max="140"
              value={zoom}
              onChange={(event) => setZoom(Number(event.target.value))}
            />
          </div>
        </div>
      </footer>
      {adminPromptOpen ? (
        <div className="admin-overlay" role="dialog" aria-modal="true">
          <form className="admin-modal" onSubmit={handleAdminSubmit}>
            <div className="admin-modal-head">
              <div>
                <p className="eyebrow">Admin</p>
                <h3>비밀번호를 입력하세요</h3>
              </div>
              <button type="button" className="admin-close" onClick={() => setAdminPromptOpen(false)}>
                닫기
              </button>
            </div>
            <label className="admin-field">
              <span>비밀번호</span>
              <input
                value={adminInput}
                onChange={(event) => setAdminInput(event.target.value)}
                placeholder="admin1234"
                type="password"
                autoFocus
              />
            </label>
            {adminError ? <p className="error-text">{adminError}</p> : null}
            <div className="admin-actions">
              <button type="submit">확인</button>
              <button type="button" className="secondary-button" onClick={() => setAdminPromptOpen(false)}>
                취소
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
