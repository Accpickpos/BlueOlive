"""
Admin user management viewset.
Allows superusers to manage other superusers.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
from shop_users.user_management_serializers import UserManagementSerializer, UserListSerializer
from tenancy.permissions import IsAdminUser

User = get_user_model()


class UserManagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing superusers.
    
    Only superusers can:
    - List all superusers
    - Create new superusers
    - Update superuser details (email, password, name)
    - Delete superusers
    - Activate/Deactivate superusers
    
    Endpoints:
    - GET /api/admin/users/ - List all superusers
    - POST /api/admin/users/ - Create new superuser
    - GET /api/admin/users/{id}/ - Get user details
    - PUT /api/admin/users/{id}/ - Update user details
    - PATCH /api/admin/users/{id}/ - Partial update
    - DELETE /api/admin/users/{id}/ - Delete user
    - POST /api/admin/users/{id}/set_password/ - Change password
    - POST /api/admin/users/{id}/toggle_active/ - Activate/Deactivate user
    """
    
    permission_classes = [IsAdminUser]
    serializer_class = UserManagementSerializer
    
    def get_queryset(self):
        """Return all Django superusers."""
        return User.objects.filter(is_superuser=True).order_by('-date_joined')
    
    def get_serializer_class(self):
        """Use different serializer for list action."""
        if self.action == 'list':
            return UserListSerializer
        return UserManagementSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new superuser. Password is required on creation."""
        if not request.data.get('password'):
            return Response(
                {'error': 'Password is required when creating a new superuser.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """
        Change password for a superuser.
        
        POST /api/admin/users/{id}/set_password/
        {
            "password": "new_secure_password"
        }
        """
        user = self.get_object()
        new_password = request.data.get('password')
        
        if not new_password:
            return Response(
                {'error': 'Password field is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user=user)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'success': f'Password updated for {user.username}'})
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Activate or deactivate a superuser account.
        
        POST /api/admin/users/{id}/toggle_active/
        """
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status_text = 'activated' if user.is_active else 'deactivated'
        return Response({
            'success': f'User {user.username} has been {status_text}.',
            'is_active': user.is_active
        })
    
    @action(detail=False, methods=['get'])
    def my_account(self, request):
        """
        Get current user's account details.
        
        GET /api/admin/users/my_account/
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
