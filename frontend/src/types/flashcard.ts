export interface FlashcardItem {
  id: string;
  word: string;
  dictionary_entry: string;
  grammatical_class: string;
  translation: string;
  example_sentence: string;
  image_url: string | null;
  audio_url: string | null;
  audio_base64: string | null;
}

export interface LessonFlashcardsResponse {
  lesson_id: string;
  lesson_title: string;
  total_cards: number;
  flashcards: FlashcardItem[];
}
