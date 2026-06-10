import type { GuessResult } from "../lib/api";

type Props = {
  guesses: GuessResult[];
};

export function GuessTable({ guesses }: Props) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h3>추측 기록</h3>
        <span>{guesses.length}회 제출</span>
      </div>
      <table className="guess-table">
        <thead>
          <tr>
            <th>시도</th>
            <th>단어</th>
            <th>순위</th>
            <th>유사도</th>
          </tr>
        </thead>
        <tbody>
          {guesses.map((guess) => (
            <tr
              key={`${guess.attempt}-${guess.word}`}
              className={guess.correct ? "guess-row guess-row-correct" : "guess-row"}
            >
              <td>{guess.attempt}</td>
              <td className="guess-word">{guess.word}</td>
              <td>{guess.correct ? "정답" : `${guess.rank}위`}</td>
              <td>{guess.similarity.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
