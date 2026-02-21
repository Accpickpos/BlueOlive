#!/usr/bin/env python
"""Create or verify shop exists for tenant."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant, Shop

tenant = Tenant.objects.get(name='Tech')
if not tenant.shops.exists():
    shop = Shop.objects.create(
        tenant=tenant,
        name='Main Shop',
        schema_name='public',
        is_head_office=True
    )
    print(f'✓ Created shop: {shop.name} with schema: {shop.schema_name}')
else:
    shops = list(tenant.shops.values_list("name", flat=True))
    print(f'✓ Shops already exist: {shops}')
