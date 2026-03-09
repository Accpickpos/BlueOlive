/**
 * useMessaging Hook
 * React Query hooks for messaging functionality
 * Manages conversations, messages, notifications, and related operations
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getConversations,
  getConversation,
  createConversation,
  getMessages,
  sendMessage,
  markConversationRead,
  uploadAttachment,
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '../messagingApi';
import type { CreateConversationPayload, SendMessagePayload } from '../types/messaging';

/**
 * Query keys for React Query
 * Used for caching and cache invalidation
 */
const QUERY_KEYS = {
  conversations: ['conversations'] as const,
  conversation: (id: number) => ['conversations', id] as const,
  messages: (conversationId: number) => ['messages', conversationId] as const,
  notifications: ['notifications'] as const,
  unreadCount: ['unreadNotificationCount'] as const,
};

/**
 * Hook to fetch all conversations for the current user
 */
export function useConversations() {
  return useQuery({
    queryKey: QUERY_KEYS.conversations,
    queryFn: getConversations,
    refetchInterval: 30000, // Poll every 30s for new conversations
    staleTime: 10000, // Consider data fresh for 10s
  });
}

/**
 * Hook to fetch a specific conversation by ID
 */
export function useConversation(id: number | null) {
  return useQuery({
    queryKey: QUERY_KEYS.conversation(id || 0),
    queryFn: () => getConversation(id!),
    enabled: !!id, // Only run query if id is provided
    staleTime: 10000,
  });
}

/**
 * Hook to fetch all messages in a conversation
 */
export function useMessages(conversationId: number | null) {
  return useQuery({
    queryKey: QUERY_KEYS.messages(conversationId || 0),
    queryFn: () => getMessages(conversationId!),
    enabled: !!conversationId, // Only run query if conversationId is provided
    refetchInterval: 5000, // Poll every 5s for new messages
    staleTime: 2000, // Consider data fresh for 2s
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateConversationPayload) => createConversation(data),
    onSuccess: () => {
      // Invalidate conversations list to refetch updated data
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations });
    },
  });
}

/**
 * Hook to send a message to a conversation (supports file attachments)
 */
export function useSendMessage(conversationId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SendMessagePayload) => sendMessage(conversationId!, data),
    onSuccess: () => {
      // Invalidate messages for this conversation
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(conversationId) });
        // Also invalidate conversations list to update last_message
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations });
        // Update unread notification count
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
      }
    },
  });
}

/**
 * Hook to mark a conversation as read
 */
export function useMarkRead(conversationId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => markConversationRead(conversationId!),
    onSuccess: () => {
      // Invalidate conversations list to update unread_count
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations });
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(conversationId) });
      }
      // Update notification count
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    },
  });
}

/**
 * Hook to upload attachment to a message
 */
export function useUploadAttachment(conversationId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ messageId, files }: { messageId: number; files: File[] }) =>
      uploadAttachment(conversationId!, messageId, files),
    onSuccess: () => {
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.messages(conversationId) });
      }
    },
  });
}

/**
 * Hook to fetch notifications
 */
export function useNotifications() {
  return useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: getNotifications,
    refetchInterval: 30000, // Poll every 30s for new notifications
    staleTime: 5000,
  });
}

/**
 * Hook to get unread notification count
 */
export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: QUERY_KEYS.unreadCount,
    queryFn: getUnreadNotificationCount,
    refetchInterval: 10000, // Poll every 10s
    staleTime: 5000,
  });
}

/**
 * Hook to mark a notification as read
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: number) => markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    },
  });
}

/**
 * Hook to mark all notifications as read
 */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    },
  });
}
