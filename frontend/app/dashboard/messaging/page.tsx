'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useConversations, useMessages, useSendMessage, useMarkRead, useCreateConversation } from '@/lib/hooks/useMessaging';
import { getUsers } from '@/lib/api';
import type { Conversation, Message, MessageAttachment, Participant } from '@/lib/types/messaging';
import { formatTime } from '@/lib/utils';
import { Plus, X, Search, Users } from 'lucide-react';

export default function MessagingPage() {
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [showNewConversation, setShowNewConversation] = useState(false);
  const { data: conversations, isLoading, isError } = useConversations();

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-white">
      {/* Conversation List - Left Sidebar */}
      <div className="w-80 border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">Messages</h1>
          <button
            onClick={() => setShowNewConversation(true)}
            className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="New Conversation"
          >
            <Plus className="h-5 w-5" />
          </button>
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
              <button
                onClick={() => setShowNewConversation(true)}
                className="mt-2 text-blue-600 hover:underline text-sm"
              >
                Start a new conversation
              </button>
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
              <Users className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">Select a conversation to start messaging</p>
              <p className="text-sm mt-2">or create a new conversation</p>
              <button
                onClick={() => setShowNewConversation(true)}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                New Conversation
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Conversation Modal */}
      {showNewConversation && (
        <NewConversationModal
          onClose={() => setShowNewConversation(false)}
          onCreated={(conversationId) => {
            setSelectedConversationId(conversationId);
            setShowNewConversation(false);
          }}
        />
      )}
    </div>
  );
}

/**
 * New Conversation Modal Component
 */
interface NewConversationModalProps {
  onClose: () => void;
  onCreated: (conversationId: number) => void;
}

function NewConversationModal({ onClose, onCreated }: NewConversationModalProps) {
  const [title, setTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [isGroup, setIsGroup] = useState(false);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const createMutation = useCreateConversation();

  // Load users
  useEffect(() => {
    async function loadUsers() {
      try {
        const data = await getUsers();
        setUsers(data);
      } catch (error) {
        console.error('Failed to load users:', error);
      } finally {
        setIsLoadingUsers(false);
      }
    }
    loadUsers();
  }, []);

  const filteredUsers = users.filter(user => {
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.toLowerCase();
    const query = searchQuery.toLowerCase();
    return fullName.includes(query) || (user.email || '').toLowerCase().includes(query);
  });

  const toggleUser = (userId: number) => {
    setSelectedUsers(prev => 
      prev.includes(userId) 
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const handleCreate = async () => {
    if (selectedUsers.length === 0) return;
    
    setIsCreating(true);
    try {
      const result = await createMutation.mutateAsync({
        title: title || undefined,
        participants: selectedUsers,
        is_group: isGroup || selectedUsers.length > 2,
      });
      onCreated(result.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">New Conversation</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Conversation Title (optional) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conversation Title (optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Team Discussion"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Group Chat Toggle */}
          <div className="mb-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isGroup}
                onChange={(e) => setIsGroup(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-gray-700">Create as group chat</span>
            </label>
          </div>

          {/* User Search */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Participants
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* User List */}
          <div className="max-h-48 overflow-y-auto border rounded-lg">
            {isLoadingUsers && (
              <div className="p-4 text-center text-gray-500">Loading users...</div>
            )}
            {!isLoadingUsers && filteredUsers.length === 0 && (
              <div className="p-4 text-center text-gray-500">No users found</div>
            )}
            {filteredUsers.map(user => (
              <button
                key={user.id}
                onClick={() => toggleUser(user.id)}
                className={`w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-50 transition-colors ${
                  selectedUsers.includes(user.id) ? 'bg-blue-50' : ''
                }`}
              >
                <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                  selectedUsers.includes(user.id) 
                    ? 'bg-blue-500 border-blue-500' 
                    : 'border-gray-300'
                }`}>
                  {selectedUsers.includes(user.id) && (
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-gray-900">
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </button>
            ))}
          </div>

          {/* Selected Count */}
          <p className="text-sm text-gray-500 mt-2">
            {selectedUsers.length} participant{selectedUsers.length !== 1 ? 's' : ''} selected
          </p>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={selectedUsers.length === 0 || isCreating}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isCreating ? 'Creating...' : 'Create Conversation'}
          </button>
        </div>
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
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
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

  const handleSend = useCallback(() => {
    if (!newMessage.trim() && selectedFiles.length === 0) return;

    sendMutation.mutate(
      { content: newMessage, files: selectedFiles },
      {
        onSuccess: () => {
          setNewMessage('');
          setSelectedFiles([]);
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
        },
      }
    );
  }, [newMessage, selectedFiles, sendMutation]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
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

      {/* Selected Files Preview */}
      {selectedFiles.length > 0 && (
        <div className="border-t border-gray-200 px-4 py-2 bg-gray-50 flex flex-wrap gap-2">
          {selectedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-1 bg-white border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <span className="truncate max-w-[150px]">{file.name}</span>
              <button
                onClick={() => removeFile(index)}
                className="text-gray-400 hover:text-red-500 ml-1"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex gap-2">
          {/* File Attach Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Attach files"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            multiple
            className="hidden"
          />
          
          {/* Message Input */}
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
            disabled={sendMutation.isPending || (!newMessage.trim() && selectedFiles.length === 0)}
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
 * Displays a single message in the conversation with attachments
 */
interface MessageBubbleProps {
  message: Message;
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
      
      {/* Attachments */}
      {message.attachments && message.attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {message.attachments.map((attachment) => (
            <AttachmentItem key={attachment.id} attachment={attachment} />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Attachment Item Component
 * Displays a single attachment with appropriate preview
 */
interface AttachmentItemProps {
  attachment: MessageAttachment;
}

function AttachmentItem({ attachment }: AttachmentItemProps) {
  const isImage = attachment.content_type?.startsWith('image/');
  
  if (isImage && attachment.url) {
    return (
      <div className="mt-2">
        <img
          src={attachment.url}
          alt={attachment.filename}
          className="max-w-[200px] rounded-lg border border-gray-200"
        />
        <a
          href={attachment.url}
          download={attachment.filename}
          className="text-xs text-blue-500 hover:text-blue-700 mt-1 inline-block"
        >
          Download {attachment.filename}
        </a>
      </div>
    );
  }
  
  return (
    <a
      href={attachment.url}
      download={attachment.filename}
      className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm"
    >
      <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <span className="text-gray-700 truncate max-w-[150px]">{attachment.filename}</span>
      <span className="text-xs text-gray-400">({formatFileSize(attachment.file_size)})</span>
    </a>
  );
}

/**
 * Format file size for display
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
