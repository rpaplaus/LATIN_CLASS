import { apiClient } from './client';
import { AuthTokens, User } from '../types/auth';

export const authApi = {
  login: async (username: string, password: string): Promise<AuthTokens> => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await apiClient.post<AuthTokens>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  register: async (
    email: string,
    password: string,
    fullName?: string
  ): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register', {
      email,
      password,
      full_name: fullName || null,
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout', {
      refresh_token: refreshToken,
    });
  },
};
