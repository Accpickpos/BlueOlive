# Widen REPORT (the other read-only tier, alongside ENQUIRY) to every role
# on every module — same rationale as 0003. REPORT-classified GET endpoints
# (action names matching "report"/"summary"/"analysis"/"statement", e.g.
# valuation-report, hourly-analysis) were still 403'ing for non-admin roles
# after 0003 only opened ENQUIRY, which under-delivered the "reads are open
# to any authenticated user regardless of role" intent behind that change —
# Report and Enquiry are both non-mutating tiers in the manual's own
# Maintenance/Transactions/Enquiry/Report vocabulary. Only MAINTENANCE and
# TRANSACTIONS (the two tiers that actually mutate data) stay role-tiered.

from django.db import migrations


def open_report(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    AccessGrant.objects.using(db_alias).filter(function_type="REPORT").update(
        is_allowed=True
    )


def revert_report(apps, schema_editor):
    # No reliable inverse — see 0003's revert_enquiry for the same reasoning.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0003_open_enquiry_to_all_roles"),
    ]

    operations = [
        migrations.RunPython(open_report, revert_report),
    ]
