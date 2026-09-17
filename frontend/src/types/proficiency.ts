export interface TopicProficiencyItem {
  topic_key: string;
  category: string;
  mastery_score: number;
  attempts_count: number;
  correct_count: number;
  consecutive_successes: number;
  status: 'mastered' | 'in_progress' | 'vulnerable';
  weakness_flags: string[];
}

export interface StudentProficiencyProfileResponse {
  user_id: string;
  overall_mastery: number;
  total_topics_tracked: number;
  mastered_topics: string[];
  vulnerable_topics: string[];
  topic_details: TopicProficiencyItem[];
  recommended_focus: string;
}

export type StudentProficiencyOverview = StudentProficiencyProfileResponse;
