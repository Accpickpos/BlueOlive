/**
 * Messaging API Client
 * Handles all API calls related to conversations and messages
 * Follows the same pattern as other API modules (creditorsApi, debtorsApi, etc.)
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type { Conversation, Message, CreateConversationPayload, SendMessagePayload } from './types/messaging';

/**
 * ===== CONVERSATIONS =====
 */

/**
 * Fetch all conversations for the current user
 */
export async function getConversations(): Promise<Conversation[]> {
  const res = await api.get(ENDPOINTS.MESSAGING.CONVERSATIONS);
  return Array.isArray(res.data) ? res.data : res.data.results || [];
}

/**
 * Fetch a specific conversation by ID
 */
export async function getConversation(id: number): Promise<Conversation> {
  const res = await api.get(ENDPOINTS.MESSAGING.CONVERSATION_DETAIL(id));
  return res.data;
}

/**
 * Create a new conversation
 */
export async function createConversation(data: CreateConversationPayload): Promise<Conversation> {
  const res = await api.post(ENDPOINTS.MESSAGING.CONVERSATIONS, data);
  return res.data;
}

/**
 * ===== MESSAGES =====
 */

/**
 * Fetch all messages in a conversation
 */
export async function getMessages(conversationId: number): Promise<Message[]> {
  const res = await api.get(ENDPOINTS.MESSAGING.MESSAGES(conversationId));
  return Array.isArray(res.data) ? res.data : res.data.results || [];
}

/**
 * Send a message to a conversation
 */
export async function sendMessage(
  conversationId: number,
  data: SendMessagePayload
): Promise<Message> {
  const res = await api.post(ENDPOINTS.MESSAGING.SEND(conversationId), data);
  return res.data;
}

/**
 * Mark all unread messages in a conversation as read
 */
export async function markConversationRead(conversationId: number): Promise<void> {
  await api.post(ENDPOINTS.MESSAGING.MARK_READ(conversationId));
}
