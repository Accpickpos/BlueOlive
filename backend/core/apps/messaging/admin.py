from django.contrib import admin

from .models import Conversation, Message, MessageAttachment, Notification


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "is_group", "created_at", "updated_at"]
    list_filter = ["is_group", "created_at"]
    search_fields = ["title"]
    readonly_fields = ["created_at", "updated_at"]
    filter_horizontal = ["participants"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["content", "sender__full_name", "conversation__title"]
    readonly_fields = ["created_at"]


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "filename",
        "message",
        "content_type",
        "file_size",
        "uploaded_at",
    ]
    list_filter = ["content_type", "uploaded_at"]
    search_fields = ["filename", "message__content"]
    readonly_fields = ["uploaded_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "notification_type", "title", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message", "user__full_name"]
    readonly_fields = ["created_at"]
