import { FormEvent, useEffect, useState } from "react";

import { GuessTable } from "../components/GuessTable";
import { api, type DailyState } from "../lib/api";

type Props = {
  playerName: string;
};

export function SoloPage({ playerName }: Props) {
  const [state, setState] = useState<DailyState | null>(null);
  const [word, setWord] = useState("");
  const [error, setError] = useState<string | null>(null);
  const latest = state?.guesses.at(-1) ?? null;

  useEffect(() => {
    api.getDailyState(playerName).then(setState).catch((reason: Error) => setError(reason.message));
  }, [playerName]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
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
              <span>최신 순위</span>
              <strong>{latest ? (latest.correct ? "정답" : `${latest.rank}위`) : "-"}</strong>
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
        <div className="status-banner">
          {state?.completed ? (
            <p className="success-text">정답을 찾았습니다. 더 추측해도 되지만 오늘 게임은 클리어 상태입니다.</p>
          ) : (
            <p className="meta-text">가까운 단어를 찾으면 순위와 유사도로 방향이 잡힙니다.</p>
          )}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </div>
      <GuessTable guesses={state?.guesses ?? []} />
    </section>
  );
}
