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
  const pinnedGuesses = room.recent_guesses.filter((guess) => !guess.correct && guess.rank < 1000);
  const overflowGuesses = room.recent_guesses.filter((guess) => !guess.correct && guess.rank >= 1000);

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
      <section className="worksheet-region worksheet-room-pinned">
        <div className="worksheet-region-head">
          <h3>1000위 미만 유지</h3>
          <span>{pinnedGuesses.length}개 단어</span>
        </div>
        <table className="guess-table">
          <thead>
            <tr>
              <th>단어</th>
              <th>순위</th>
              <th>유사도</th>
              <th>입력자</th>
            </tr>
          </thead>
          <tbody>
            {pinnedGuesses.length > 0 ? (
              pinnedGuesses.map((guess) => (
                <tr key={`${guess.word}-${guess.player_id}`} className="guess-row">
                  <td className="guess-word">{guess.word}</td>
                  <td>{formatRank(guess.rank, false)}</td>
                  <td>{guess.similarity.toFixed(2)}</td>
                  <td>{guess.name}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4}>아직 1000위 안에 든 단어가 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
      <section className="worksheet-region worksheet-room-overflow">
        <div className="worksheet-region-head">
          <h3>1000위 이상 힌트</h3>
          <span>유사도순 {overflowGuesses.length > 24 ? "상위 24개" : `${overflowGuesses.length}개`}</span>
        </div>
        <ul className="guess-feed">
          {overflowGuesses.length > 0 ? (
            overflowGuesses.map((guess) => (
              <li key={`${guess.word}-${guess.player_id}`}>
                <strong className="guess-word">{guess.word}</strong>
                <span>{formatRank(guess.rank, guess.correct)}</span>
                <span>{guess.similarity.toFixed(2)}</span>
                <span>{guess.name}</span>
              </li>
            ))
          ) : (
            <li className="guess-feed-empty">
              <span>1000위 이상 힌트는 아직 없습니다.</span>
            </li>
          )}
        </ul>
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
          <h3>공유 힌트판</h3>
          <span>중복 단어 자동 병합</span>
        </div>
        <p className="meta-text">같은 단어를 여러 번 넣어도 한 번만 유지됩니다. 정답 단어는 기록에 표시하지 않고, 상위 추측만 공유합니다.</p>
      </section>
    </>
  );
}
