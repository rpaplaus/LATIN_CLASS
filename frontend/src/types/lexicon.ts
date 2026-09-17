export interface LexiconEntry {
  word: string;
  dictionary_entry: string;
  grammatical_class: string;
  translation: string;
  example_sentence: string;
  lesson_id: string;
  lesson_title: string;
  module_title: string;
  audio_url: string;
  is_favorite: boolean;
}

export interface LexiconResponse {
  total_words: number;
  favorite_count: number;
  available_classes: string[];
  entries: LexiconEntry[];
}

export interface FavoriteToggleResponse {
  word: string;
  is_favorite: boolean;
  message: string;
}
