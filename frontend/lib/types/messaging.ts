/**
 * Messaging Module - Type Definitions
 * Types for conversations and messages system
 */

// ============ Message ============
export interface Message {
  id: number;
  conversation: number;
  sender: number;
  sender_name: string;
  content: string;
  is_read: boolean;
  created_at: string;
}

// ============ Conversation ============
export interface Conversation {
  id: number;
  title: string;
  participants: number[];
  is_group: boolean;
  last_message: Message | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

// ============ Payloads ============
export interface CreateConversationPayload {
  title?: string;
  participants: number[];
  is_group?: boolean;
}

export interface SendMessagePayload {
  content: string;
}

// ============ API Responses ============
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
