import { apiClient } from './client';
import { CourseModule, UserProgress } from '../types/progress';
import { LessonContent } from '../types/lesson';
import {
  ExerciseEvaluationRequest,
  ExerciseEvaluationResponse,
} from '../types/evaluation';

export const lessonApi = {
  getModules: async (): Promise<CourseModule[]> => {
    const response = await apiClient.get<CourseModule[]>('/lessons/modules');
    return response.data;
  },

  getProgress: async (): Promise<UserProgress> => {
    const response = await apiClient.get<UserProgress>('/lessons/progress');
    return response.data;
  },

  generateNextLesson: async (): Promise<LessonContent> => {
    const response = await apiClient.post<LessonContent>('/lessons/next');
    return response.data;
  },

  evaluateExercise: async (
    lessonId: string,
    payload: ExerciseEvaluationRequest
  ): Promise<ExerciseEvaluationResponse> => {
    const response = await apiClient.post<ExerciseEvaluationResponse>(
      `/lessons/${lessonId}/evaluate`,
      payload
    );
    return response.data;
  },

  completeLesson: async (
    lessonId: string,
    score: number = 100
  ): Promise<UserProgress> => {
    const response = await apiClient.post<UserProgress>(
      `/lessons/${lessonId}/complete`,
      { score }
    );
    return response.data;
  },
};
