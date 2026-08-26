"""
Common app - Shared utilities across all business apps.

This app provides reusable components:
- Permissions: Base permission classes and role-based access control
- Serializers: Common serializer mixins and base classes
- Services: Shared business logic services

Usage:
    from apps.common.permissions import BaseModelPermission, HasRole
    from apps.common.serializers import AuditFieldsMixin
    from apps.common.services import BaseService
"""

default_app_config = "apps.common.apps.CommonConfig"
