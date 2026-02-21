from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'is_group', 'created_at', 'updated_at']
    list_filter = ['is_group', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__full_name', 'conversation__title']
    readonly_fields = ['created_at']
