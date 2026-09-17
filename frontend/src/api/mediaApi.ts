import { apiClient } from './client';
import { PronunciationEvaluationResponse, TTSResponse } from '../types/media';

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

  evaluatePronunciation: async (
    audioBlob: Blob,
    targetText: string
  ): Promise<PronunciationEvaluationResponse> => {
    const formData = new FormData();
    // Default file name audio.webm or audio.wav
    const extension = audioBlob.type.includes('wav') ? 'wav' : 'webm';
    formData.append('audio_file', audioBlob, `speech_recording.${extension}`);
    formData.append('target_text', targetText);

    const response = await apiClient.post<PronunciationEvaluationResponse>(
      '/media/stt/evaluate',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
