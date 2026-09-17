import { apiClient } from './client';
import {
  ArenaChallengeResponse,
  ArenaEvaluationRequest,
  ArenaEvaluationResponse,
} from '../types/arena';

export const arenaApi = {
  /**
   * Request a targeted 3-flashcard combat round focusing on student's vulnerability.
   */
  generateChallenge: async (topicKey?: string | null): Promise<ArenaChallengeResponse> => {
    const response = await apiClient.post<ArenaChallengeResponse>('/arena/generate', {
      topic_key: topicKey || null,
    });
    return response.data;
  },

  /**
   * Evaluate a single flashcard answer and dynamically recalculate student EMA.
   */
  evaluateCard: async (payload: ArenaEvaluationRequest): Promise<ArenaEvaluationResponse> => {
    const response = await apiClient.post<ArenaEvaluationResponse>('/arena/evaluate', payload);
    return response.data;
  },
};
