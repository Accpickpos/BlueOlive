from rest_framework import serializers

from .models import Conversation, Message, MessageAttachment, Notification


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = MessageAttachment
        fields = [
            "id",
            "file",
            "filename",
            "content_type",
            "file_size",
            "url",
            "uploaded_at",
        ]
        read_only_fields = ["filename", "content_type", "file_size", "uploaded_at"]

    def get_url(self, obj):
        """Get the full URL for the attachment."""
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "is_read",
            "created_at",
            "attachments",
        ]
        read_only_fields = ["sender", "created_at", "is_read"]


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    participants_detail = serializers.SerializerMethodField()
    # Accept participants as a list of IDs
    participants = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "participants",
            "participants_detail",
            "is_group",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "title": {"required": False, "allow_blank": True},
            "is_group": {"required": False},
        }

    def get_last_message(self, obj):
        msg = obj.messages.order_by("-created_at").first()
        return MessageSerializer(msg).data if msg else None

    def get_unread_count(self, obj):
        user = self.context["request"].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()

    def get_participants_detail(self, obj):
        """Get detailed participant information."""
        from shop_users.serializers import ShopUserSerializer

        return ShopUserSerializer(obj.participants.all(), many=True).data


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "title",
            "message",
            "link",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]
