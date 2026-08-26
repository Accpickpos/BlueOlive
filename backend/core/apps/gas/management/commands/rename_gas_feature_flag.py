"""
One-time fix-up for `tenancy.SubscriptionPlan.features` after the rentals->gas
app rename.

`GasFeatureEnabled` (apps/gas/permissions.py) now checks
`subscription.plan.features.get('gas', False)` instead of the old
`.get('rentals', False)`. The seed script
(tenancy/management/commands/seed_subscriptions.py) never actually sets
either key on any plan, so this is a no-op for anyone relying only on seeded
data. But `SubscriptionPlan.features` is a plain JSONField editable via the
admin UI — if any real, already-deployed plan had `"rentals": true` added by
hand outside the seed script, that plan would silently lose Gas access after
this rename (the permission check would look for a key that no longer
matches). This command finds and fixes exactly that case.

`SubscriptionPlan` lives in the shared/platform database (`tenancy` is a
SHARED_APPS app, not per-shop), so — unlike `rename_rentals_app_to_gas`,
which operates per-shop-schema — this only needs to run once, against the
default connection.

Usage:
    python manage.py rename_gas_feature_flag           # preview
    python manage.py rename_gas_feature_flag --apply    # actually rewrite
"""

from django.core.management.base import BaseCommand
from tenancy.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Rename the 'rentals' key to 'gas' in SubscriptionPlan.features, wherever it's set."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write the change (default: preview only)",
        )

    def handle(self, *args, **options):
        affected = SubscriptionPlan.objects.filter(features__has_key="rentals")

        if not affected.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "No SubscriptionPlan has a 'rentals' key in features — nothing to do."
                )
            )
            return

        for plan in affected:
            old_value = plan.features.get("rentals")
            self.stdout.write(
                f"Plan '{plan.name}' ({plan.slug}): features['rentals']={old_value!r}"
                + (
                    " -> features['gas']"
                    if options["apply"]
                    else " (would rename to features['gas'], preview only)"
                )
            )
            if options["apply"]:
                plan.features["gas"] = old_value
                del plan.features["rentals"]
                plan.save(update_fields=["features"])

        if not options["apply"]:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{affected.count()} plan(s) affected. Re-run with --apply to make the change."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nUpdated {affected.count()} plan(s).")
            )
