import os
from django.db import models
from django.conf import settings


def message_attachment_path(instance, filename):
    """Generate upload path for message attachments."""
    return f'messaging/attachments/{instance.message.conversation.id}/{instance.message.id}/{filename}'


class Conversation(models.Model):
    """A conversation between users within a tenant."""
    title = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Conversation {self.id}"


class Message(models.Model):
    """A message within a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} at {self.created_at}"


class MessageAttachment(models.Model):
    """File attachment for a message."""
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to=message_attachment_path)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment: {self.filename}"

    @property
    def file_extension(self):
        """Get file extension."""
        return os.path.splitext(self.filename)[1].lower()

    @property
    def is_image(self):
        """Check if attachment is an image."""
        return self.content_type and self.content_type.startswith('image/')


class Notification(models.Model):
    """Notification for messages and other events."""
    NOTIFICATION_TYPES = (
        ('new_message', 'New Message'),
        ('message_mention', 'Message Mention'),
        ('conversation_invite', 'Conversation Invite'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user}: {self.title}"
