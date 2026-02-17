/**
 * useMessaging Hook
 * React Query hooks for messaging functionality
 * Manages conversations, messages, and related operations
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
 * Hook to send a message to a conversation
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
    },
  });
}
