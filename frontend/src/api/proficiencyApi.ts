import { apiClient } from './client';
import { StudentProficiencyProfileResponse } from '../types/proficiency';

export const proficiencyApi = {
  getMyProficiency: async (): Promise<StudentProficiencyProfileResponse> => {
    const response = await apiClient.get<StudentProficiencyProfileResponse>('/users/me/proficiency');
    return response.data;
  },
};
