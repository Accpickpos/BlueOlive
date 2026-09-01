# Seed the full role x module x function_type matrix (4 x 8 x 4 = 128 rows)
# to reproduce today's de facto access as closely as the existing per-app
# permission checks imply. Nothing reads this table yet — it's a starting
# default an admin corrects via the new Access Grants UI.

from django.db import migrations

ROLES = ["ADMIN", "MANAGER", "STAFF", "CASHIER"]
MODULES = [
    "pos",
    "debtors",
    "creditors",
    "cash_book",
    "general_ledger",
    "stock_control",
    "purchase_orders",
    "settings",
]
FUNCTION_TYPES = ["MAINTENANCE", "TRANSACTIONS", "ENQUIRY", "REPORT"]

# MANAGER is allowed everywhere except these (module, function_type) pairs —
# matches apps/general_ledger/permissions.py's CanPerformPeriodEnd/
# CanPerformYearEnd (admin-only) and apps/creditors/permissions.py's
# admin-only maintenance checks.
MANAGER_DENY = {
    ("general_ledger", "MAINTENANCE"),
    ("settings", "MAINTENANCE"),
}

# CASHIER only gets Transactions/Enquiry on the two modules a real cashier
# touches day-to-day (apps/cash_book/permissions.py's IsCashier group scope;
# POS is a cashier's primary module though it has no such file today).
CASHIER_ALLOW_MODULES = {"pos", "cash_book"}


def is_allowed(role, module, function_type):
    if role == "ADMIN":
        return True
    if role == "MANAGER":
        return (module, function_type) not in MANAGER_DENY
    if role == "STAFF":
        return function_type in ("TRANSACTIONS", "ENQUIRY")
    if role == "CASHIER":
        return module in CASHIER_ALLOW_MODULES and function_type in (
            "TRANSACTIONS",
            "ENQUIRY",
        )
    return False


def seed_grants(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    rows = [
        AccessGrant(
            role=role,
            module=module,
            function_type=function_type,
            is_allowed=is_allowed(role, module, function_type),
        )
        for role in ROLES
        for module in MODULES
        for function_type in FUNCTION_TYPES
    ]
    AccessGrant.objects.using(db_alias).bulk_create(rows, ignore_conflicts=True)


def unseed_grants(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    AccessGrant.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_grants, unseed_grants),
    ]
