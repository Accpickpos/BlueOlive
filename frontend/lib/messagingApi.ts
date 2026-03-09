/**
 * Messaging API Client
 * Handles all API calls related to conversations, messages, attachments, and notifications
 * Follows the same pattern as other API modules (creditorsApi, debtorsApi, etc.)
 */

import { api } from './api';
import { ENDPOINTS } from './api-config';
import type { Conversation, Message, CreateConversationPayload, SendMessagePayload, Notification } from './types/messaging';

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
 * Send a message to a conversation (supports file attachments)
 */
export async function sendMessage(
  conversationId: number,
  data: SendMessagePayload
): Promise<Message> {
  const formData = new FormData();
  formData.append('content', data.content);
  
  if (data.files && data.files.length > 0) {
    data.files.forEach((file) => {
      formData.append('files', file);
    });
  }
  
  const res = await api.post(ENDPOINTS.MESSAGING.SEND(conversationId), formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
}

/**
 * Mark all unread messages in a conversation as read
 */
export async function markConversationRead(conversationId: number): Promise<void> {
  await api.post(ENDPOINTS.MESSAGING.MARK_READ(conversationId));
}

/**
 * Upload attachment to an existing message
 */
export async function uploadAttachment(
  conversationId: number,
  messageId: number,
  files: File[]
): Promise<any> {
  const formData = new FormData();
  formData.append('message_id', messageId.toString());
  files.forEach((file) => {
    formData.append('files', file);
  });
  
  const res = await api.post(
    ENDPOINTS.MESSAGING.UPLOAD_ATTACHMENT(conversationId),
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return res.data;
}

/**
 * ===== NOTIFICATIONS =====
 */

/**
 * Fetch all notifications for the current user
 */
export async function getNotifications(): Promise<Notification[]> {
  const res = await api.get(ENDPOINTS.MESSAGING.NOTIFICATIONS);
  return Array.isArray(res.data) ? res.data : res.data.results || [];
}

/**
 * Get unread notification count
 */
export async function getUnreadNotificationCount(): Promise<number> {
  const res = await api.get(ENDPOINTS.MESSAGING.NOTIFICATION_UNREAD_COUNT);
  return res.data.unread_count;
}

/**
 * Mark a single notification as read
 */
export async function markNotificationRead(notificationId: number): Promise<void> {
  await api.post(ENDPOINTS.MESSAGING.NOTIFICATION_MARK_READ(notificationId));
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsRead(): Promise<void> {
  await api.post(ENDPOINTS.MESSAGING.NOTIFICATION_MARK_ALL_READ);
}
