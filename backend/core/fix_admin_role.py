import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from shop_users.models import ShopUser

# Get tenant
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()

# Get the first user (the original admin)
user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, username='codemind23@outlook.com').first()

if user:
    print(f"Before: {user.username} - role={user.role}")
    
    # Set role back to ADMIN
    user.role = 'ADMIN'
    user.save(using=tenant.db_alias)
    
    print(f"After: {user.username} - role={user.role}")
else:
    print("User not found!")
