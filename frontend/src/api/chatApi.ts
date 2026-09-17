import { apiClient } from './client';
import { ChatInteractiveRequest, ChatInteractiveResponse } from '../types/chat';

export const chatApi = {
  sendMessage: async (request: ChatInteractiveRequest): Promise<ChatInteractiveResponse> => {
    const response = await apiClient.post<ChatInteractiveResponse>('/chat/interactive', request);
    return response.data;
  },
};
