# Widen ENQUIRY (read) access to every role on every module. The original
# seed (0002) restricted ENQUIRY the same way as TRANSACTIONS/MAINTENANCE,
# which the module-by-module viewset rollout showed was too strict as a
# default: it 403'd STAFF/CASHIER-role users out of ordinary read endpoints
# the moment HasModuleFunctionAccess was wired into a module's ViewSets,
# breaking existing read access for anyone not ADMIN/MANAGER. Only
# MAINTENANCE, TRANSACTIONS and REPORT stay role-tiered per the original
# matrix — reads are now open to any authenticated user regardless of role,
# matching pre-rollout behavior and the low-risk framing of the original
# plan; admins can still tighten specific reads later via the Access Grants
# screen.

from django.db import migrations


def open_enquiry(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    AccessGrant.objects.using(db_alias).filter(function_type="ENQUIRY").update(
        is_allowed=True
    )


def revert_enquiry(apps, schema_editor):
    # No reliable inverse (0002's original per-role ENQUIRY values aren't
    # preserved anywhere) — reversing this migration is a no-op rather than
    # guessing at prior state.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0002_seed_access_grants"),
    ]

    operations = [
        migrations.RunPython(open_enquiry, revert_enquiry),
    ]
