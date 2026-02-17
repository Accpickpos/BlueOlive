#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from shop_users.models import ShopUser
from django.contrib.auth import get_user_model
from tenancy.models import Tenant

User = get_user_model()
print("User model:", User)
print("User count:", User.objects.count())
print("Tenant count:", Tenant.objects.count())

tenants = Tenant.objects.all()
print("\nTenants:")
for t in tenants:
    db_alias = getattr(t, 'db_alias', f'tenant_{t.id}')
    print(f"  {t.slug} (id={t.id}, db_alias={db_alias})")
    try:
        user_count = ShopUser.objects.using(db_alias).count()
        print(f"    Users in this tenant: {user_count}")
        users = ShopUser.objects.using(db_alias).all()[:3]
        for u in users:
            print(f"      - {u.username}: tenant_id={u.tenant_id}, role={u.role}")
    except Exception as e:
        print(f"    Error querying users: {e}")
