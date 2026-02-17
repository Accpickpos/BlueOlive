'use client';

import { useState, useEffect, useRef } from 'react';
import { useConversations, useMessages, useSendMessage, useMarkRead } from '@/lib/hooks/useMessaging';
import type { Conversation } from '@/lib/types/messaging';
import { formatTime } from '@/lib/utils';

export default function MessagingPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const { data: conversations, isLoading, isError } = useConversations();

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-white">
      {/* Conversation List - Left Sidebar */}
      <div className="w-80 border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Messages</h1>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="p-4 text-center text-gray-500">
              <p>Loading conversations...</p>
            </div>
          )}
          {isError && (
            <div className="p-4 bg-red-50 text-red-700">
              <p>Error loading conversations</p>
            </div>
          )}
          {conversations && conversations.length === 0 && (
            <div className="p-4 text-center text-gray-500">
              <p>No conversations yet</p>
            </div>
          )}
          {conversations?.map((conversation) => (
            <ConversationItem
              key={conversation.id}
              conversation={conversation}
              isSelected={selectedConversationId === conversation.id}
              onSelect={() => setSelectedConversationId(conversation.id)}
            />
          ))}
        </div>
      </div>

      {/* Message Thread - Main Content */}
      <div className="flex-1 flex flex-col">
        {selectedConversationId ? (
          <MessageThread conversationId={selectedConversationId} />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <p className="text-lg">Select a conversation to start messaging</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Conversation Item Component
 * Displays a single conversation in the left sidebar
 */
interface ConversationItemProps {
  conversation: Conversation;
  isSelected: boolean;
  onSelect: () => void;
}

function ConversationItem({ conversation, isSelected, onSelect }: ConversationItemProps) {
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
        isSelected ? 'bg-blue-50 border-b-2 border-blue-200' : ''
      }`}
    >
      <div className="flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">
            {conversation.title || 'Untitled Conversation'}
          </h3>
          {conversation.last_message && (
            <p className="text-sm text-gray-600 truncate mt-1">
              <span className="font-medium">{conversation.last_message.sender_name}:</span>{' '}
              {conversation.last_message.content}
            </p>
          )}
        </div>
        {conversation.unread_count > 0 && (
          <span className="flex-shrink-0 bg-blue-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {conversation.unread_count > 9 ? '9+' : conversation.unread_count}
          </span>
        )}
      </div>
    </button>
  );
}

/**
 * Message Thread Component
 * Displays messages in a conversation and handles sending new messages
 */
interface MessageThreadProps {
  conversationId: number;
}

function MessageThread({ conversationId }: MessageThreadProps) {
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { data: messages, isLoading } = useMessages(conversationId);
  const sendMutation = useSendMessage(conversationId);
  const markReadMutation = useMarkRead(conversationId);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Mark conversation as read when viewing
  useEffect(() => {
    markReadMutation.mutate();
  }, [conversationId]);

  const handleSend = () => {
    if (!newMessage.trim()) return;

    sendMutation.mutate(
      { content: newMessage },
      {
        onSuccess: () => {
          setNewMessage('');
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="flex justify-center py-8">
            <p className="text-gray-500">Loading messages...</p>
          </div>
        )}

        {messages && messages.length === 0 && !isLoading && (
          <div className="flex justify-center py-8">
            <p className="text-gray-500">No messages yet. Start the conversation!</p>
          </div>
        )}

        {messages?.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={sendMutation.isPending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            onClick={handleSend}
            disabled={sendMutation.isPending || !newMessage.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {sendMutation.isPending ? 'Sending...' : 'Send'}
          </button>
        </div>
        {sendMutation.isError && (
          <p className="text-red-500 text-sm mt-2">Failed to send message</p>
        )}
      </div>
    </>
  );
}

/**
 * Message Bubble Component
 * Displays a single message in the conversation
 */
interface MessageBubbleProps {
  message: any;
}

function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline gap-2">
        <span className="text-sm font-medium text-gray-700">{message.sender_name}</span>
        <span className="text-xs text-gray-400">{formatTime(message.created_at)}</span>
      </div>
      <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-md break-words">
        <p className="text-gray-900">{message.content}</p>
      </div>
    </div>
  );
}
