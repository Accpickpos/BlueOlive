from django.conf import settings
from django.db import migrations, models


def backfill_enabled_addons(apps, schema_editor):
    """
    Existing tenants already have every OPTIONAL_ADDON_APPS app migrated into
    every shop schema (that was the only behavior before this migration) -
    backfill enabled_addons to match so nothing is silently cut off for them.
    New tenants created after this migration get whatever the creation flow
    passes (defaults to an empty list otherwise).
    """
    Tenant = apps.get_model("tenancy", "Tenant")
    addons = list(getattr(settings, "OPTIONAL_ADDON_APPS", []))
    if addons:
        Tenant.objects.update(enabled_addons=addons)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenancy', '0017_shop_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='enabled_addons',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Subset of settings.OPTIONAL_ADDON_APPS enabled for this tenant',
            ),
        ),
        migrations.RunPython(backfill_enabled_addons, noop_reverse),
    ]
