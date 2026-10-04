export type ChatSender = 'user' | 'bot';

export interface ChatReply {
  reply: string;
  message_id: number | null;
}

export interface ChatBubble {
  id: string;
  sender: ChatSender;
  content: string;
}
