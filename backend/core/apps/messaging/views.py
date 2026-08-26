import logging
import os
import re

from apps.shop_filter_mixin import ShopFilterMixin
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Message, MessageAttachment, Notification
from .serializers import (
    ConversationSerializer,
    MessageAttachmentSerializer,
    MessageSerializer,
    NotificationSerializer,
)

logger = logging.getLogger(__name__)

# Business-document allowlist — mirrors the kind of files a shop actually
# exchanges over messaging (quotes, invoices, photos of parts/vehicles).
ALLOWED_ATTACHMENT_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "txt",
    "csv",
}

# Explicitly blocked regardless of allowlist — these are the actual
# XSS/execution risk if served back to a browser.
DANGEROUS_ATTACHMENT_EXTENSIONS = {
    "html",
    "htm",
    "svg",
    "js",
    "mjs",
    "exe",
    "bat",
    "cmd",
    "sh",
    "php",
    "phtml",
    "jsp",
}

MAX_ATTACHMENT_SIZE = getattr(
    settings, "MAX_MESSAGE_ATTACHMENT_SIZE", 10 * 1024 * 1024
)  # 10MB default

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._\- ]")


def _sanitize_filename(name):
    """
    Strip anything that isn't a safe filename character before storing the
    raw client-supplied name in the `filename` field (this is reflected via
    the API, separately from the sanitized storage path Django generates).
    """
    name = os.path.basename(name or "")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip()
    return name[:255] or "attachment"


def _validate_attachment(file):
    """
    Validate an uploaded message attachment.
    Returns an error message string if invalid, otherwise None.
    """
    ext = os.path.splitext(file.name or "")[1].lower().lstrip(".")

    if not ext or ext in DANGEROUS_ATTACHMENT_EXTENSIONS:
        return f"File type '.{ext or '?'}' is not allowed for security reasons."

    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        return (
            f"File type '.{ext}' is not supported. Allowed types: "
            + ", ".join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))
        )

    if file.size and file.size > MAX_ATTACHMENT_SIZE:
        return f"File exceeds the maximum size of {MAX_ATTACHMENT_SIZE // (1024 * 1024)}MB."

    # Verify magic bytes for images — catches a spoofed extension on a
    # non-image payload (e.g. an HTML/script file renamed to .png).
    if ext in ("png", "jpg", "jpeg", "gif"):
        try:
            from PIL import Image

            file.seek(0)
            Image.open(file).verify()
        except Exception:
            return "File content does not match a valid image."
        finally:
            file.seek(0)

    return None


class ConversationViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users only see conversations they participate in
        return Conversation.objects.filter(participants=self.request.user).distinct()

    def create(self, request, *args, **kwargs):
        """Create a new conversation with participants."""
        # Resolve & validate participants BEFORE creating anything — a user
        # may only add other ShopUsers who share a tenant AND at least one
        # shop with them, otherwise this endpoint lets anyone pull any user
        # on the platform into a conversation.
        participant_ids = request.data.get("participants", [])
        if isinstance(participant_ids, str):
            # Handle comma-separated string
            participant_ids = [
                int(p.strip()) for p in participant_ids.split(",") if p.strip()
            ]

        from shop_users.models import ShopUser

        requester_shop_ids = set(
            request.user.get_active_shops().values_list("id", flat=True)
        )

        resolved_participants = []
        invalid_participant_ids = []
        for participant_id in participant_ids:
            try:
                participant = ShopUser.objects.get(id=participant_id)
            except ShopUser.DoesNotExist:
                invalid_participant_ids.append(participant_id)
                continue

            if participant.tenant_id != request.user.tenant_id:
                invalid_participant_ids.append(participant_id)
                continue

            participant_shop_ids = set(
                participant.get_active_shops().values_list("id", flat=True)
            )
            if not (requester_shop_ids & participant_shop_ids):
                invalid_participant_ids.append(participant_id)
                continue

            resolved_participants.append(participant)

        if invalid_participant_ids:
            return Response(
                {
                    "error": "Some participants are not valid members of your shop(s)",
                    "invalid_participant_ids": invalid_participant_ids,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        # Add the current user as a participant
        conversation.participants.add(request.user)

        for participant in resolved_participants:
            conversation.participants.add(participant)

        # Create conversation invite notifications for other participants
        for participant in conversation.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                notification_type="conversation_invite",
                title=f'New conversation: {conversation.title or "Untitled"}',
                message=f"{request.user.full_name} added you to a conversation",
                link=f"/dashboard/messaging?conversation={conversation.id}",
            )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        conversation = serializer.save()
        conversation.participants.add(self.request.user)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def send(self, request, pk=None):
        conversation = self.get_object()

        # Handle content from either form data or JSON
        content = request.data.get("content", "")

        # Validate attachments before creating anything
        files = request.FILES.getlist("files")
        for file in files:
            error = _validate_attachment(file)
            if error:
                return Response(
                    {"error": f"{file.name}: {error}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Create the message
        message = Message.objects.create(
            conversation=conversation, sender=request.user, content=content
        )

        # Handle file attachments
        for file in files:
            MessageAttachment.objects.create(
                message=message,
                file=file,
                filename=_sanitize_filename(file.name),
                content_type=file.content_type,
                file_size=file.size,
            )

        # Update conversation timestamp
        conversation.save()  # triggers auto_now on updated_at

        # Create notifications for other participants
        for participant in conversation.participants.exclude(id=request.user.id):
            Notification.objects.create(
                user=participant,
                notification_type="new_message",
                title=f"New message from {request.user.full_name}",
                message=content[:100] + ("..." if len(content) > 100 else ""),
                link=f"/dashboard/messaging?conversation={conversation.id}",
            )

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def upload_attachment(self, request, pk=None):
        """Upload attachment to an existing message."""
        conversation = self.get_object()
        message_id = request.data.get("message_id")

        if not message_id:
            return Response(
                {"error": "message_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            message = conversation.messages.get(id=message_id)
        except Message.DoesNotExist:
            return Response(
                {"error": "Message not found"}, status=status.HTTP_404_NOT_FOUND
            )

        files = request.FILES.getlist("files")
        for file in files:
            error = _validate_attachment(file)
            if error:
                return Response(
                    {"error": f"{file.name}: {error}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        attachments = []
        for file in files:
            attachment = MessageAttachment.objects.create(
                message=message,
                file=file,
                filename=_sanitize_filename(file.name),
                content_type=file.content_type,
                file_size=file.size,
            )
            attachments.append(attachment)

        serializer = MessageAttachmentSerializer(attachments, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        conversation = self.get_object()
        conversation.messages.filter(is_read=False).exclude(sender=request.user).update(
            is_read=True
        )
        return Response({"status": "messages marked as read"})


class NotificationViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return Notification.objects.filter(user=self.request.user)
        except Exception:
            # Table doesn't exist yet, return empty queryset
            return Notification.objects.none()

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Get count of unread notifications."""
        try:
            count = Notification.objects.filter(
                user=request.user, is_read=False
            ).count()
        except Exception:
            # Table doesn't exist yet
            count = 0
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        try:
            notification = self.get_object()
            notification.is_read = True
            notification.save()
            return Response({"status": "notification marked as read"})
        except Exception:
            return Response({"status": "notification not found"}, status=404)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        try:
            Notification.objects.filter(user=request.user, is_read=False).update(
                is_read=True
            )
        except Exception:
            logger.exception("Failed to mark all notifications as read")
        return Response({"status": "all notifications marked as read"})
