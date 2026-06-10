import type { RoomState } from "../lib/api";

type Props = {
  room: RoomState;
  currentPlayerId: string | null;
};

function formatRank(rank: number | null, solved = false) {
  if (solved) {
    return "정답";
  }
  if (rank === null) {
    return "-";
  }
  if (rank >= 1000) {
    return "1000위 이상";
  }
  return `${rank}위`;
}

export function RoomBoard({ room, currentPlayerId }: Props) {
  const myLatestGuess = currentPlayerId
    ? room.recent_guesses.find((guess) => guess.player_id === currentPlayerId) ?? null
    : null;
  const rankedFeed = room.recent_guesses
    .filter((guess) => guess !== myLatestGuess)
    .slice()
    .sort((left, right) => {
      if (left.correct !== right.correct) {
        return left.correct ? -1 : 1;
      }
      if (left.rank !== right.rank) {
        return left.rank - right.rank;
      }
      if (left.similarity !== right.similarity) {
        return right.similarity - left.similarity;
      }
      return right.created_at.localeCompare(left.created_at);
    });

  return (
    <div className="room-grid">
      <section className="sheet-block">
        <div className="sheet-block-columns">
          <span>J</span>
          <span>K</span>
          <span>L</span>
        </div>
        <div className="sheet-block-body">
          <div className="sheet-row">
            <div className="sheet-row-number">4</div>
            <div className="sheet-row-cells sheet-title-row">
              <div className="panel-header panel-header-tight">
                <h3>상위권 힌트</h3>
                <span>정답 길이 {room.answer_length}자</span>
              </div>
            </div>
          </div>
          <div className="sheet-row">
            <div className="sheet-row-number">5</div>
            <div className="sheet-row-cells">
              <div className="diagnostics-grid">
                <div className="stat-chip">
                  <span>1위 유사도</span>
                  <strong>{room.hint_metrics.rank_1_similarity.toFixed(2)}</strong>
                </div>
                <div className="stat-chip">
                  <span>10위 컷</span>
                  <strong>{room.hint_metrics.top_10_cutoff_similarity.toFixed(2)}</strong>
                </div>
                <div className="stat-chip">
                  <span>100위 컷</span>
                  <strong>{room.hint_metrics.top_100_cutoff_similarity.toFixed(2)}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="sheet-block">
        <div className="sheet-block-columns">
          <span>A</span>
          <span>B</span>
          <span>C</span>
          <span>D</span>
          <span>E</span>
        </div>
        <div className="sheet-block-body">
          <div className="sheet-row">
            <div className="sheet-row-number">5</div>
            <div className="sheet-row-cells sheet-title-row">
              <div className="panel-header panel-header-tight">
                <h3>참가자 순위</h3>
                <span>정답 길이 {room.answer_length}자</span>
              </div>
            </div>
          </div>
          <div className="sheet-row">
            <div className="sheet-row-number">6</div>
            <div className="sheet-row-cells sheet-table-cell">
              <table className="guess-table">
                <thead>
                  <tr>
                    <th>상태</th>
                    <th>이름</th>
                    <th>시도</th>
                    <th>최고 순위</th>
                    <th>최고 유사도</th>
                  </tr>
                </thead>
                <tbody>
                  {room.members.map((member) => (
                    <tr key={member.player_id} className={member.solved ? "guess-row guess-row-correct" : "guess-row"}>
                      <td>{member.solved ? "완료" : "진행중"}</td>
                      <td className="guess-word">{member.name}</td>
                      <td>{member.attempts}</td>
                      <td>{formatRank(member.best_rank, member.solved)}</td>
                      <td>{member.best_similarity?.toFixed(2) ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
      <section className="sheet-block">
        <div className="sheet-block-columns">
          <span>F</span>
          <span>G</span>
          <span>H</span>
          <span>I</span>
        </div>
        <div className="sheet-block-body">
          <div className="sheet-row">
            <div className="sheet-row-number">5</div>
            <div className="sheet-row-cells sheet-title-row">
              <div className="panel-header panel-header-tight">
                <h3>최근 추측</h3>
                <span>내 최신 추측 우선</span>
              </div>
            </div>
          </div>
          <div className="sheet-row">
            <div className="sheet-row-number">6</div>
            <div className="sheet-row-cells sheet-table-cell">
              <ul className="guess-feed">
                {myLatestGuess ? (
                  <li key={`${myLatestGuess.player_id}-${myLatestGuess.created_at}`} className="guess-feed-highlight">
                    <strong>내 최근 추측</strong>
                    <span className="guess-word">{myLatestGuess.word}</span>
                    <span>{formatRank(myLatestGuess.rank, myLatestGuess.correct)}</span>
                    <span>{myLatestGuess.similarity.toFixed(2)}</span>
                  </li>
                ) : null}
                {rankedFeed.map((guess) => (
                  <li key={`${guess.player_id}-${guess.created_at}`}>
                    <strong>{guess.name}</strong>
                    <span className="guess-word">{guess.word}</span>
                    <span>{formatRank(guess.rank, guess.correct)}</span>
                    <span>{guess.similarity.toFixed(2)}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
