"""
SaaS Admin - User Management API
Endpoints for creating and managing tenant users (app managers/admins)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from tenancy.models import Tenant, Shop

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_tenant_admin(request):
    """
    Create a new tenant admin user.
    
    POST /api/v1/saas-admin/users/create-admin/
    
    Required fields:
    - username: Unique username
    - email: User email
    - password: User password
    - tenant_id: Tenant ID to associate user with
    
    Optional fields:
    - first_name: User first name
    - last_name: User last name
    - shop_ids: List of shop IDs to assign user to
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    tenant_id = request.data.get('tenant_id')
    
    # Validate required fields
    errors = []
    if not username:
        errors.append('username is required')
    if not email:
        errors.append('email is required')
    if not password:
        errors.append('password is required')
    if not tenant_id:
        errors.append('tenant_id is required')
    
    if errors:
        return Response(
            {'errors': errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate tenant exists
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
    except Tenant.DoesNotExist:
        return Response(
            {'error': f'Tenant with id {tenant_id} not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get optional fields
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    shop_ids = request.data.get('shop_ids', [])
    
    try:
        with transaction.atomic():
            # Create user with admin role
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='ADMIN',  # Set as admin
                tenant_id=tenant_id,
                is_active=True
            )
            
            # Assign to shops if provided
            if shop_ids:
                valid_shops = Shop.objects.filter(
                    id__in=shop_ids,
                    tenant=tenant,
                    is_active=True
                )
                user.shops.set(valid_shops)
            
            return Response({
                'message': f'Admin user "{username}" created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'tenant_id': user.tenant_id,
                    'is_active': user.is_active,
                }
            }, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response(
            {'error': 'A user with this username or email already exists'},
            status=status.HTTP_409_CONFLICT
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to create user: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def list_tenant_users(request):
    """
    List or search users for a specific tenant.
    
    GET /api/v1/saas-admin/users/?tenant_id=<id>
    POST /api/v1/saas-admin/users/search/
    
    Query params:
    - tenant_id: Filter by tenant (required)
    - role: Filter by role (ADMIN, MANAGER, USER)
    - is_active: Filter by active status
    - search: Search by username or email
    """
    tenant_id = request.query_params.get('tenant_id') or (request.data.get('tenant_id') if request.method == 'POST' else None)
    
    if not tenant_id:
        return Response(
            {'error': 'tenant_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
    except Tenant.DoesNotExist:
        return Response(
            {'error': f'Tenant with id {tenant_id} not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Build queryset
    queryset = User.objects.filter(tenant=tenant)
    
    # Apply filters
    role = request.query_params.get('role') or request.data.get('role')
    if role:
        queryset = queryset.filter(role=role)
    
    is_active = request.query_params.get('is_active') or request.data.get('is_active')
    if is_active is not None:
        is_active_bool = is_active.lower() in ('true', '1', 'yes')
        queryset = queryset.filter(is_active=is_active_bool)
    
    search = request.query_params.get('search') or request.data.get('search')
    if search:
        queryset = queryset.filter(
            username__icontains=search
        ) | queryset.filter(
            email__icontains=search
        )
    
    # Return results
    users_data = []
    for user in queryset.order_by('username'):
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.date_joined,
            'last_login': user.last_login,
        })
    
    return Response({
        'tenant': {
            'id': tenant.id,
            'name': tenant.name,
        },
        'count': len(users_data),
        'users': users_data
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def toggle_user_status(request):
    """
    Activate or deactivate a user.
    
    POST /api/v1/saas-admin/users/toggle-status/
    
    Required fields:
    - user_id: ID of the user to toggle
    """
    user_id = request.data.get('user_id')
    
    if not user_id:
        return Response(
            {'error': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': f'User with id {user_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Toggle status
    user.is_active = not user.is_active
    user.save()
    
    return Response({
        'message': f'User "{user.username}" is now {"active" if user.is_active else "inactive"}',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_active': user.is_active
        }
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_user_password(request):
    """
    Reset a user's password.
    
    POST /api/v1/saas-admin/users/reset-password/
    
    Required fields:
    - user_id: ID of the user
    - new_password: New password
    """
    user_id = request.data.get('user_id')
    new_password = request.data.get('new_password')
    
    if not user_id or not new_password:
        return Response(
            {'error': 'user_id and new_password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': f'User with id {user_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': f'Password for user "{user.username}" has been reset'
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def assign_user_shops(request):
    """
    Assign a user to shops.
    
    POST /api/v1/saas-admin/users/assign-shops/
    
    Required fields:
    - user_id: ID of the user
    - shop_ids: List of shop IDs
    """
    user_id = request.data.get('user_id')
    shop_ids = request.data.get('shop_ids', [])
    
    if not user_id:
        return Response(
            {'error': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': f'User with id {user_id} not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate shops belong to user's tenant
    if shop_ids:
        valid_shops = Shop.objects.filter(
            id__in=shop_ids,
            tenant=user.tenant,
            is_active=True
        )
        user.shops.set(valid_shops)
    else:
        user.shops.clear()
    
    return Response({
        'message': f'Shops assigned to user "{user.username}"',
        'user': {
            'id': user.id,
            'username': user.username,
            'assigned_shops': [
                {'id': s.id, 'name': s.name, 'code': s.code}
                for s in user.shops.all()
            ]
        }
    })
