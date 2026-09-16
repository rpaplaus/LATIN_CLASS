export interface MorphologicalToken {
  token: string;
  lemma: string;
  part_of_speech: string;
  grammatical_features: string;
  is_correct: boolean;
  feedback_note?: string | null;
}

export interface ExerciseEvaluationRequest {
  lesson_id: string;
  exercise_id: number;
  question: string;
  expected_answer: string;
  student_answer: string;
  exercise_type?: string;
}

export interface ExerciseEvaluationResponse {
  is_correct: boolean;
  score: number;
  overall_feedback: string;
  syntax_critique: string;
  morphological_breakdown: MorphologicalToken[];
  suggested_classical_alternatives: string[];
  evaluator_model: string;
}
