export interface ArenaFlashcard {
  id: number;
  latin: string;
  translation: string;

  hint: string;
  audio_url: string;
}

export interface ArenaChallengeResponse {
  challenge_id: string;
  topic_key: string;
  topic_label: string;
  current_mastery: number;
  vulnerability_score: number;
  cards: ArenaFlashcard[];
}

export interface ArenaEvaluationRequest {
  topic_key: string;
  card_id: number;
  latin: string;
  expected_answer: string;
  student_answer: string;
}

export interface ArenaEvaluationResponse {
  card_id: number;
  is_correct: boolean;
  score: number;
  feedback: string;
  previous_mastery: number;
  new_mastery: number;
}
