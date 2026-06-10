import { FormEvent, useEffect, useState } from "react";

import { GuessTable } from "../components/GuessTable";
import { api, type DailyState, type EmbeddingInfo, type HintResult, type RevealResult } from "../lib/api";

type Props = {
  playerName: string;
};

export function SoloPage({ playerName }: Props) {
  const [state, setState] = useState<DailyState | null>(null);
  const [word, setWord] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [hintMessage, setHintMessage] = useState<string | null>(null);
  const [shareMessage, setShareMessage] = useState<string | null>(null);
  const [embeddingInfo, setEmbeddingInfo] = useState<EmbeddingInfo | null>(null);
  const latest = state?.guesses.at(-1) ?? null;

  useEffect(() => {
    api.getDailyState(playerName).then(setState).catch((reason: Error) => setError(reason.message));
  }, [playerName]);

  useEffect(() => {
    api.getEmbeddingInfo().then(setEmbeddingInfo).catch(() => undefined);
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setHintMessage(null);
    try {
      const guess = await api.submitDailyGuess(playerName, word);
      setState((current) =>
        current
          ? {
              ...current,
              guesses: [...current.guesses, guess],
              completed: current.completed || guess.correct,
            }
          : null,
      );
      setWord("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "guess failed");
    }
  }

  async function handleHint(kind: "nearby" | "initial") {
    setError(null);
    try {
      const result: HintResult =
        kind === "nearby" ? await api.getHint(playerName) : await api.getInitialHint(playerName);
      setState((current) =>
        current
          ? {
              ...current,
              hint_count: current.hint_count + 1,
              initial_hint_used: current.initial_hint_used || result.kind === "initial",
            }
          : current,
      );
      setHintMessage(
        result.kind === "initial"
          ? `초성 힌트: ${result.word}`
          : `힌트 단어: ${result.word} · ${result.rank}위 · ${result.similarity.toFixed(2)}`,
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "hint failed");
    }
  }

  async function handleGiveUp() {
    setError(null);
    try {
      const reveal: RevealResult = await api.giveUp(playerName);
      setState((current) =>
        current
          ? {
              ...current,
              revealed: true,
              reveal,
            }
          : current,
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "give up failed");
    }
  }

  async function handleShare() {
    if (!state) {
      return;
    }
    const latestRank = latest ? (latest.correct ? "정답" : `${latest.rank}위`) : "-";
    const summary = [
      `뉴맨틀 클론`,
      `${playerName} · ${state.game_date}`,
      `시도 ${state.guesses.length}회`,
      `힌트 ${state.hint_count}회`,
      `최신 상태 ${latestRank}`,
      state.completed ? "오늘의 단어를 맞혔습니다." : state.revealed ? `정답은 ${state.reveal?.word}` : "아직 진행 중입니다.",
    ].join("\n");

    try {
      if (navigator.share) {
        await navigator.share({ title: "뉴맨틀 클론 결과", text: summary });
      } else {
        await navigator.clipboard.writeText(summary);
      }
      setShareMessage("결과 문구를 공유할 수 있게 준비했습니다.");
    } catch {
      setShareMessage("공유를 취소했거나 클립보드 접근이 실패했습니다.");
    }
  }

  return (
    <section className="stack">
      <div className="hero-card hero-card-solo">
        <div className="hero-topline">
          <div>
            <p className="eyebrow">Daily Puzzle</p>
            <h2>오늘의 정답 단어를 찾아보세요</h2>
          </div>
          <div className="stat-strip">
            <div className="stat-chip">
              <span>플레이어</span>
              <strong>{playerName}</strong>
            </div>
            <div className="stat-chip">
              <span>시도</span>
              <strong>{state?.guesses.length ?? 0}</strong>
            </div>
            <div className="stat-chip">
              <span>힌트 사용</span>
              <strong>{state?.hint_count ?? 0}</strong>
            </div>
          </div>
        </div>
        <p className="hero-copy">
          한국어 일반명사만 대상으로 의미 유사도를 계산합니다. 입력할수록 더 뜨거운 방향으로 정답을 좁혀가는
          구조입니다.
        </p>
        <form className="guess-form" onSubmit={handleSubmit}>
          <input value={word} onChange={(event) => setWord(event.target.value)} placeholder="정답일 것 같은 단어를 입력" />
          <button type="submit">추측</button>
        </form>
        <div className="action-row">
          <button type="button" className="secondary-button" onClick={() => handleHint("nearby")}>
            근접 힌트
          </button>
          <button type="button" className="secondary-button" onClick={() => handleHint("initial")}>
            초성 힌트
          </button>
          <button type="button" className="secondary-button" onClick={handleGiveUp}>
            포기하기
          </button>
          <button type="button" className="secondary-button" onClick={handleShare}>
            결과 공유
          </button>
        </div>
        <div className="status-banner">
          {state?.completed ? (
            <p className="success-text">정답을 찾았습니다. 더 추측해도 되지만 오늘 게임은 클리어 상태입니다.</p>
          ) : state?.revealed && state.reveal ? (
            <p className="success-text">정답은 {state.reveal.word}였습니다. {state.reveal.description}</p>
          ) : (
            <p className="meta-text">
              정답은 {state?.answer_length ?? "-"}자 단어입니다. 가까운 단어를 찾으면 순위와 유사도로 방향이 잡힙니다.
            </p>
          )}
          {hintMessage ? <p className="meta-text">{hintMessage}</p> : null}
          {shareMessage ? <p className="meta-text">{shareMessage}</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </div>
      <GuessTable guesses={state?.guesses ?? []} />
      {embeddingInfo ? (
        <div className="panel diagnostics-panel">
          <div className="panel-header">
            <h3>환경 진단</h3>
            <span>{embeddingInfo.source}</span>
          </div>
          <div className="diagnostics-grid">
            <div className="stat-chip">
              <span>허용 단어</span>
              <strong>{embeddingInfo.total_words.toLocaleString()}</strong>
            </div>
            <div className="stat-chip">
              <span>정답 후보</span>
              <strong>{embeddingInfo.answer_words.toLocaleString()}</strong>
            </div>
            <div className="stat-chip">
              <span>사전 교차</span>
              <strong>{String(embeddingInfo.metadata.lexicon_intersection ?? false)}</strong>
            </div>
          </div>
          <p className="meta-text">
            회사 환경에서 실제 fastText 데이터가 준비되면 이 값들이 seed 수준보다 훨씬 크게 보여야 합니다.
          </p>
        </div>
      ) : null}
    </section>
  );
}
