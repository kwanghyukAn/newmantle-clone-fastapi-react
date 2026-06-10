const API_BASE = "http://localhost:8000";

export type GuessResult = {
  word: string;
  similarity: number;
  rank: number;
  correct: boolean;
  attempt: number;
};

export type DailyState = {
  game_date: string;
  guesses: GuessResult[];
  completed: boolean;
};

export type RoomState = {
  room_id: string;
  answer_length: number;
  created_at: string;
  members: Array<{
    player_id: string;
    name: string;
    attempts: number;
    best_rank: number | null;
    best_similarity: number | null;
    solved: boolean;
    last_active_at: string;
  }>;
  recent_guesses: Array<{
    player_id: string;
    name: string;
    word: string;
    similarity: number;
    rank: number;
    correct: boolean;
    attempt: number;
    created_at: string;
  }>;
};

export function roomWebSocketUrl(roomId: string) {
  return `ws://localhost:8000/api/rooms/${roomId}/ws`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "request failed");
  }

  return response.json() as Promise<T>;
}

export const api = {
  getDailyState(playerName: string) {
    const query = new URLSearchParams({ player_name: playerName });
    return request<DailyState>(`/api/daily/state?${query.toString()}`);
  },
  submitDailyGuess(playerName: string, word: string) {
    return request<GuessResult>("/api/daily/guess", {
      method: "POST",
      body: JSON.stringify({ player_name: playerName, word }),
    });
  },
  createRoom(hostName: string) {
    return request<{ room_id: string; player_id: string }>("/api/rooms", {
      method: "POST",
      body: JSON.stringify({ host_name: hostName }),
    });
  },
  joinRoom(roomId: string, name: string) {
    return request<{ room_id: string; player_id: string }>(`/api/rooms/${roomId}/join`, {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },
  getRoom(roomId: string) {
    return request<RoomState>(`/api/rooms/${roomId}`);
  },
  submitRoomGuess(roomId: string, playerId: string, word: string) {
    return request<GuessResult>(`/api/rooms/${roomId}/guess`, {
      method: "POST",
      body: JSON.stringify({ player_id: playerId, word }),
    });
  },
};
