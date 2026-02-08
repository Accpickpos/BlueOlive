from tenancy.models import Tenant
tenants = Tenant.objects.all()
print(f"Found {len(tenants)} tenants:")
for tenant in tenants:
    print(f"  - {tenant.id}: {tenant.name} ({tenant.slug}) - db: {tenant.db_name} - alias: {tenant.db_alias}")
