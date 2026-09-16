import { apiClient } from './client';
import { TTSResponse } from '../types/media';

export const mediaApi = {
  getTTSAudio: async (text: string, voice: string = 'onyx'): Promise<TTSResponse> => {
    const response = await apiClient.post<TTSResponse>('/media/tts', {
      text,
      voice,
    });
    return response.data;
  },

  getAudioUrl: (audioHash: string): string => {
    return `/api/v1/media/audio/${audioHash}`;
  },
};
