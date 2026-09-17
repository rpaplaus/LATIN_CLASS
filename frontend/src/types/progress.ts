export interface LessonSummary {
  id: string;
  module_id: string;
  order_index: number;
  title: string;
  pedagogical_objective: string;
  grammar_topics: string[];
  is_completed: boolean;
}

export interface CourseModule {
  id: string;
  order_index: number;
  title: string;
  description: string;
  level: string;
  lessons: LessonSummary[];
}

export interface UserProgress {
  user_id: string;
  current_module_id: string | null;
  current_lesson_id: string | null;
  current_module_title: string | null;
  current_lesson_title: string | null;
  completed_lessons_count: number;
  total_points: number;
  current_streak_days: number;
}

export interface CompletedLessonSummary {
  id: string;
  completion_id: string;
  order_index: number;
  title: string;
  module_id: string;
  module_title: string;
  score: number;
  completed_at: string;
  pedagogical_objective: string;
  grammar_topics: string[];
}
