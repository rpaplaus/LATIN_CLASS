export interface TTSResponse {
  audio_hash: string;
  audio_url: string;
  audio_base64: string;
  cached: boolean;
  text: string;
  voice: string;
  mime_type?: string;
}

export interface WordPhoneticBreakdown {
  word: string;
  status: 'correct' | 'acceptable' | 'needs_practice' | string;
  accuracy: number;
  phonetic_rule_note?: string | null;
}

export interface PronunciationEvaluationResponse {
  target_text: string;
  transcribed_text: string;
  overall_score: number;
  is_passing: boolean;
  word_breakdown: WordPhoneticBreakdown[];
  phonetic_tips: string;
  critical_phonemes_detected?: Record<string, boolean>;
}
