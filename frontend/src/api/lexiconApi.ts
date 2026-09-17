import { apiClient } from './client';
import { FavoriteToggleResponse, LexiconResponse } from '../types/lexicon';

export const lexiconApi = {
  /**
   * Fetch consolidated Latin vocabulary for the authenticated student.
   * Zero LLM cost: queries PostgreSQL JSONB content and cached audio hashes.
   */
  getLexicon: async (): Promise<LexiconResponse> => {
    const response = await apiClient.get<LexiconResponse>('/users/me/lexicon');
    return response.data;
  },

  /**
   * Toggle a Latin vocabulary word in the student's Pugillares (favorites).
   */
  toggleFavorite: async (word: string): Promise<FavoriteToggleResponse> => {
    const response = await apiClient.post<FavoriteToggleResponse>(
      '/users/me/lexicon/favorites/toggle',
      { word }
    );
    return response.data;
  },

  /**
   * List all favorited words in Pugillares.
   */
  getFavorites: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>('/users/me/lexicon/favorites');
    return response.data;
  },
};

