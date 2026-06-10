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

function formatSolveOrder(order: number | null) {
  if (order === null) {
    return "-";
  }
  return `${order}위`;
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
    <>
      <section className="worksheet-region worksheet-room-hints">
        <div className="worksheet-region-head">
          <h3>상위권 힌트</h3>
          <span>{room.first_solver ? `최초 정답 ${room.first_solver.name}` : "유사도 컷라인"}</span>
        </div>
        <div className="worksheet-key-table worksheet-key-table-compact">
          <div><span>1위 유사도</span><strong>{room.hint_metrics.rank_1_similarity.toFixed(2)}</strong></div>
          <div><span>10위 컷</span><strong>{room.hint_metrics.top_10_cutoff_similarity.toFixed(2)}</strong></div>
          <div><span>100위 컷</span><strong>{room.hint_metrics.top_100_cutoff_similarity.toFixed(2)}</strong></div>
        </div>
        {room.first_solver ? (
          <p className="meta-text">
            가장 먼저 정답을 맞춘 사람은 {room.first_solver.name}이며 완주 순위 {room.first_solver.solve_order}위입니다.
          </p>
        ) : (
          <p className="meta-text">아직 아무도 정답을 맞추지 못했습니다.</p>
        )}
      </section>
      <section className="worksheet-region worksheet-room-members">
        <div className="worksheet-region-head">
          <h3>참가자 순위</h3>
          <span>진행 순위 + 완주 순위</span>
        </div>
        <table className="guess-table">
          <thead>
            <tr>
              <th>상태</th>
              <th>이름</th>
              <th>완주 순위</th>
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
                <td>{formatSolveOrder(member.solve_order)}</td>
                <td>{member.attempts}</td>
                <td>{formatRank(member.best_rank, member.solved)}</td>
                <td>{member.best_similarity?.toFixed(2) ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="worksheet-region worksheet-room-feed">
        <div className="worksheet-region-head">
          <h3>최근 추측</h3>
          <span>내 최신 추측 우선</span>
        </div>
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
      </section>
    </>
  );
}
