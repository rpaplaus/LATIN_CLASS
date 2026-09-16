import { apiClient } from './client';
import { Badge, SenateOverview, UserBadge } from '../types/gamification';

export const badgeApi = {
  getAllBadges: async (): Promise<Badge[]> => {
    const response = await apiClient.get<Badge[]>('/badges/');
    return response.data;
  },

  getMyBadges: async (): Promise<UserBadge[]> => {
    const response = await apiClient.get<UserBadge[]>('/badges/me');
    return response.data;
  },

  getSenateOverview: async (): Promise<SenateOverview> => {
    const response = await apiClient.get<SenateOverview>('/badges/overview');
    return response.data;
  },
};
