import type { RoomState } from "../lib/api";

type Props = {
  room: RoomState;
};

export function RoomBoard({ room }: Props) {
  return (
    <div className="room-grid">
      <section className="panel">
        <div className="panel-header">
          <h3>참가자 순위</h3>
          <span>정답 길이 {room.answer_length}자</span>
        </div>
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
                <td className="guess-word">
                  {member.name}
                </td>
                <td>{member.attempts}</td>
                <td>{member.best_rank ?? "-"}</td>
                <td>{member.best_similarity?.toFixed(2) ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <div className="panel-header">
          <h3>최근 추측</h3>
          <span>실시간 피드</span>
        </div>
        <ul className="guess-feed">
          {room.recent_guesses.map((guess) => (
            <li key={`${guess.player_id}-${guess.created_at}`}>
              <strong>{guess.name}</strong>
              <span className="guess-word">{guess.word}</span>
              <span>{guess.correct ? "정답" : `${guess.rank}위`}</span>
              <span>{guess.similarity.toFixed(2)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
