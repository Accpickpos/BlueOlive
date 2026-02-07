#!/usr/bin/env python
"""
Check if we can manually create RefreshToken with explicit database usage.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from shop_users.models import ShopUser
from tenancy.models import Tenant
from tenancy.tenant_context import set_current_tenant
from django.utils import timezone
from datetime import datetime, timedelta
import jwt
from django.conf import settings

# Get a tenant
tenant = Tenant.objects.filter(db_name='tenant_great').first()
if not tenant:
    print("Tenant not found")
    exit(1)

print(f"Using tenant: {tenant.name} (alias: {tenant.db_alias})")

# Get a user from that tenant
set_current_tenant(tenant)
user = ShopUser.objects.using(tenant.db_alias).first()
if not user:
    print("No user in tenant")
    exit(1)

print(f"Using user: {user.username}")

# Try to create OutstandingToken manually with using=
try:
    print("\nTest 1: Create OutstandingToken with using=")
    
    # Generate a token manually
    refresh = RefreshToken.for_user(user)
    print(f"✓ RefreshToken created")
    
    # Check if OutstandingToken was created
    outstanding = OutstandingToken.objects.using(tenant.db_alias).filter(user=user).first()
    if outstanding:
        print(f"✓ OutstandingToken created: {outstanding.id}")
    else:
        print(f"✗ OutstandingToken not found")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
