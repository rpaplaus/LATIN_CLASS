import { apiClient } from './client';
import { LessonFlashcardsResponse } from '../types/flashcard';

export const flashcardApi = {
  getLessonFlashcards: async (lessonId: string): Promise<LessonFlashcardsResponse> => {
    const response = await apiClient.get<LessonFlashcardsResponse>(
      `/flashcards/lesson/${lessonId}`
    );
    return response.data;
  },
};
