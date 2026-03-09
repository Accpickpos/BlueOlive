/**
 * Messaging Module - Type Definitions
 * Types for conversations, messages, attachments, and notifications
 */

// ============ Message Attachment ============
export interface MessageAttachment {
  id: number;
  file: string;
  filename: string;
  content_type: string;
  file_size: number;
  url: string;
  uploaded_at: string;
}

// ============ Message ============
export interface Message {
  id: number;
  conversation: number;
  sender: number;
  sender_name: string;
  content: string;
  is_read: boolean;
  created_at: string;
  attachments: MessageAttachment[];
}

// ============ Conversation ============
export interface Conversation {
  id: number;
  title: string;
  participants: number[];
  participants_detail?: Participant[];
  is_group: boolean;
  last_message: Message | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

// ============ Participant (from ShopUser) ============
export interface Participant {
  id: number;
  email: string;
  full_name: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  shop_ids: number[];
}

// ============ Notification ============
export interface Notification {
  id: number;
  notification_type: 'new_message' | 'message_mention' | 'conversation_invite';
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

// ============ Payloads ============
export interface CreateConversationPayload {
  title?: string;
  participants: number[];
  is_group?: boolean;
}

export interface SendMessagePayload {
  content: string;
  files?: File[];
}

// ============ API Responses ============
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
