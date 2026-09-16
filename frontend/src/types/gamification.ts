export interface Badge {
  id: string;
  code: string;
  title: string;
  latin_motto: string;
  description: string;
  icon_name: string;
  category: 'streak' | 'score' | 'completion' | 'special' | string;
  tier: 'bronze' | 'silver' | 'gold' | 'laurel' | string;
  requirement_type: string;
  requirement_value: number;
  xp_reward: number;
}

export interface UserBadge {
  id: string;
  badge_id: string;
  badge: Badge;
  unlocked_at: string;
  metadata: Record<string, unknown>;
}

export interface SenateBadgeItem {
  badge: Badge;
  is_unlocked: boolean;
  unlocked_at: string | null;
  progress: number;
}

export interface SenateOverview {
  total_unlocked: number;
  total_available: number;
  completion_percentage: number;
  badges: SenateBadgeItem[];
}
