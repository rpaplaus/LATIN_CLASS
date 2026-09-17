export interface ChatInteractiveRequest {
  message: string;
  lesson_id?: string | null;
  context_topics?: string[];
}

export interface ChatInteractiveResponse {
  reply: string;
  sources_consulted: string[];
  historical_trivia_snippet?: string | null;
}

export interface ChatConversationMessage {
  id: string;
  sender: 'user' | 'magister';
  text: string;
  timestamp: string;
  sources_consulted?: string[];
  historical_trivia_snippet?: string | null;
  suggested_questions?: string[];
}
