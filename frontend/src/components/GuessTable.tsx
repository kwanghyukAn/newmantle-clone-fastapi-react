import type { GuessResult } from "../lib/api";

type Props = {
  guesses: GuessResult[];
};

export function GuessTable({ guesses }: Props) {
  const formatRank = (guess: GuessResult) => {
    if (guess.correct) {
      return "정답";
    }
    if (guess.rank >= 1000) {
      return "1000위 이상";
    }
    return `${guess.rank}위`;
  };

  return (
    <div className="sheet-block">
      <div className="sheet-block-columns">
        <span>A</span>
        <span>B</span>
        <span>C</span>
        <span>D</span>
      </div>
      <div className="sheet-block-body">
        <div className="sheet-row">
          <div className="sheet-row-number">9</div>
          <div className="sheet-row-cells sheet-title-row">
            <div className="panel-header panel-header-tight">
              <h3>추측 기록</h3>
              <span>{guesses.length}회 제출</span>
            </div>
          </div>
        </div>
        <div className="sheet-row">
          <div className="sheet-row-number">10</div>
          <div className="sheet-row-cells sheet-table-cell">
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
                    <td>{formatRank(guess)}</td>
                    <td>{guess.similarity.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
