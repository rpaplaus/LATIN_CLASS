export interface LatinExample {
  latin: string;
  translation: string;
  grammatical_notes: string;
}

export interface VocabularyItem {
  word: string;
  dictionary_entry: string;
  grammatical_class: string;
  translation: string;
  example_sentence: string;
}

export interface LessonExercise {
  id: number;
  exercise_type: 'multiple_choice' | 'fill_blank' | 'translation' | string;
  instruction: string;
  question: string;
  options: string[] | null;
  correct_answer: string;
  explanation: string;
}

export interface TheorySection {
  topic: string;
  explanation: string;
  rule_summary: string;
}

export interface HistoricalTrivia {
  title: string;
  fact?: string;
  content?: string;
  text?: string;
  century_or_period?: string;
  latin_motto_or_phrase?: string;
  source_reference?: string | null;
}

export interface LessonContent {
  lesson_id: string;
  module_title: string;
  lesson_title: string;
  pedagogical_goal: string;
  historical_context: string;
  theory_sections: TheorySection[];
  examples: LatinExample[];
  vocabulary: VocabularyItem[];
  exercises: LessonExercise[];
  teacher_tip: string;
  historical_trivia?: HistoricalTrivia[] | null;
}
