"""
Tests for apps.common: the AccessGrant role x module x function_type matrix
and its HasModuleFunctionAccess permission class.

NOTE: migration 0002_seed_access_grants pre-populates every valid
(role, module, function_type) combination (4 roles x 8 modules x 4 function
types = 128 rows); 0003_open_enquiry_to_all_roles and
0004_open_report_to_all_roles then widen every ENQUIRY and REPORT row to
is_allowed=True regardless of role (the two non-mutating tiers) — all three
run before any test starts, since Django's test runner applies all
migrations, including data migrations, when building the test DB. Tests
must account for that: creating a row that duplicates an already-seeded
combination will hit the unique_together constraint, so tests either
assert against the seeded defaults directly, or delete a row first to
simulate a genuinely missing one. ENQUIRY and REPORT are universally True
post-0004 — tests exercising a "denied" case use MAINTENANCE/TRANSACTIONS
instead, the two tiers that stay role-tiered.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from .mixins import ModuleFunctionPermissionMixin
from .models import AccessGrant
from .permissions import HasModuleFunctionAccess

User = get_user_model()


class AccessGrantModelTests(TestCase):
    def test_unique_together_enforced(self):
        # (ADMIN, pos, MAINTENANCE) already exists from the seed migration.
        with self.assertRaises(ValidationError):
            AccessGrant.objects.create(
                role="ADMIN",
                module="pos",
                function_type="MAINTENANCE",
                is_allowed=False,
            )

    def test_seed_matrix_row_count(self):
        self.assertEqual(AccessGrant.objects.count(), 4 * 8 * 4)

    def test_seed_defaults_match_documented_matrix(self):
        # ADMIN: everything allowed.
        self.assertTrue(
            AccessGrant.is_role_allowed("ADMIN", "general_ledger", "MAINTENANCE")
        )
        # MANAGER: allowed except the documented deny-list.
        self.assertFalse(
            AccessGrant.is_role_allowed("MANAGER", "general_ledger", "MAINTENANCE")
        )
        self.assertTrue(
            AccessGrant.is_role_allowed("MANAGER", "general_ledger", "TRANSACTIONS")
        )
        # STAFF: Transactions everywhere, plus both read tiers (Enquiry and
        # Report — migrations 0003/0004), but never Maintenance.
        self.assertTrue(AccessGrant.is_role_allowed("STAFF", "creditors", "ENQUIRY"))
        self.assertTrue(AccessGrant.is_role_allowed("STAFF", "creditors", "REPORT"))
        self.assertFalse(
            AccessGrant.is_role_allowed("STAFF", "creditors", "MAINTENANCE")
        )
        # CASHIER: Transactions only on pos/cash_book, but both read tiers
        # everywhere — the original per-role Enquiry/Report restriction
        # 403'd ordinary reads for non-admin roles the moment a module's
        # ViewSets were wired up, so 0003/0004 opened both broadly; only
        # Maintenance and Transactions (the two mutating tiers) stay
        # role-tiered.
        self.assertTrue(AccessGrant.is_role_allowed("CASHIER", "cash_book", "ENQUIRY"))
        self.assertTrue(AccessGrant.is_role_allowed("CASHIER", "pos", "TRANSACTIONS"))
        self.assertTrue(AccessGrant.is_role_allowed("CASHIER", "creditors", "ENQUIRY"))
        self.assertTrue(AccessGrant.is_role_allowed("CASHIER", "creditors", "REPORT"))
        self.assertFalse(
            AccessGrant.is_role_allowed("CASHIER", "creditors", "TRANSACTIONS")
        )


class _FakeRequest:
    def __init__(self, method):
        self.method = method


class _FakeViewSet(ModuleFunctionPermissionMixin):
    action_function_types = {"weird_report": "REPORT"}

    def __init__(self, action, method="GET"):
        self.action = action
        self.request = _FakeRequest(method)


class ModuleFunctionPermissionMixinTests(TestCase):
    def test_standard_crud_actions(self):
        self.assertEqual(_FakeViewSet("list").get_function_type(), "ENQUIRY")
        self.assertEqual(_FakeViewSet("retrieve").get_function_type(), "ENQUIRY")
        self.assertEqual(
            _FakeViewSet("create", "POST").get_function_type(), "TRANSACTIONS"
        )
        self.assertEqual(
            _FakeViewSet("update", "PUT").get_function_type(), "TRANSACTIONS"
        )
        self.assertEqual(
            _FakeViewSet("partial_update", "PATCH").get_function_type(), "TRANSACTIONS"
        )
        self.assertEqual(
            _FakeViewSet("destroy", "DELETE").get_function_type(), "MAINTENANCE"
        )

    def test_explicit_override_wins(self):
        self.assertEqual(
            _FakeViewSet("weird_report", "POST").get_function_type(), "REPORT"
        )

    def test_name_heuristics(self):
        self.assertEqual(
            _FakeViewSet("monthly_summary", "GET").get_function_type(), "REPORT"
        )
        self.assertEqual(
            _FakeViewSet("deactivate", "POST").get_function_type(), "MAINTENANCE"
        )
        self.assertEqual(
            _FakeViewSet("post_invoice", "POST").get_function_type(), "TRANSACTIONS"
        )

    def test_unmatched_action_falls_back_by_method(self):
        # No keyword match: safe methods -> ENQUIRY, mutating methods -> MAINTENANCE
        # (the conservative choice for an unreviewed state-changing action).
        self.assertEqual(
            _FakeViewSet("bank_balances", "GET").get_function_type(), "ENQUIRY"
        )
        self.assertEqual(
            _FakeViewSet("close_month", "PATCH").get_function_type(), "MAINTENANCE"
        )


class HasModuleFunctionAccessTests(TestCase):
    def setUp(self):
        # ShopUser.save() requires either is_superuser or an explicit
        # tenant_id (raises "Cannot create user without tenant context"
        # otherwise) — pass one directly rather than relying on the
        # thread-local tenant context these tests don't set up.
        # email is unique=True and create_user() defaults it to "" — two
        # users in one test would collide on that empty string, so each
        # needs a distinct explicit email.
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staffuser@test.local",
            password="testpass123",  # nosec B105 B106 - test fixture password
            role="STAFF",
            tenant_id=1,
        )
        self.cashier_user = User.objects.create_user(
            username="cashieruser",
            email="cashieruser@test.local",
            password="testpass123",  # nosec B105 B106 - test fixture password
            role="CASHIER",
            tenant_id=1,
        )

    def test_allows_seeded_granted_combination(self):
        # Seed matrix: STAFF is granted TRANSACTIONS everywhere.
        permission = HasModuleFunctionAccess("creditors", "TRANSACTIONS")
        request = type("Req", (), {"user": self.staff_user})()
        self.assertTrue(permission.has_permission(request, None))

    def test_denies_seeded_ungranted_combination(self):
        # Seed matrix: STAFF is never granted MAINTENANCE.
        permission = HasModuleFunctionAccess("creditors", "MAINTENANCE")
        request = type("Req", (), {"user": self.staff_user})()
        self.assertFalse(permission.has_permission(request, None))

    def test_denies_role_outside_module_scope(self):
        # Seed matrix: CASHIER's TRANSACTIONS grant is scoped to pos/cash_book
        # only (unlike ENQUIRY, which migration 0003 opened to every role on
        # every module).
        permission = HasModuleFunctionAccess("creditors", "TRANSACTIONS")
        request = type("Req", (), {"user": self.cashier_user})()
        self.assertFalse(permission.has_permission(request, None))

    def test_denies_missing_grant_row(self):
        AccessGrant.objects.filter(
            role="STAFF", module="creditors", function_type="REPORT"
        ).delete()
        permission = HasModuleFunctionAccess("creditors", "REPORT")
        request = type("Req", (), {"user": self.staff_user})()
        self.assertFalse(permission.has_permission(request, None))

    def test_denies_unauthenticated(self):
        permission = HasModuleFunctionAccess("pos", "TRANSACTIONS")
        anon_request = type(
            "Req", (), {"user": type("Anon", (), {"is_authenticated": False})()}
        )()
        self.assertFalse(permission.has_permission(anon_request, None))


class AccessGrantAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
            tenant_id=1,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_grants(self):
        response = self.client.get("/api/common/access-grants/")
        self.assertEqual(response.status_code, 200)

    def test_bulk_update_existing_row(self):
        response = self.client.post(
            "/api/common/access-grants/bulk_update/",
            {
                "grants": [
                    {
                        "role": "MANAGER",
                        "module": "pos",
                        "function_type": "REPORT",
                        "is_allowed": False,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        grant = AccessGrant.objects.get(
            role="MANAGER", module="pos", function_type="REPORT"
        )
        self.assertFalse(grant.is_allowed)

    def test_bulk_update_reports_missing_row(self):
        # Simulate a genuinely missing row by deleting an already-seeded one.
        AccessGrant.objects.filter(
            role="CASHIER", module="general_ledger", function_type="MAINTENANCE"
        ).delete()
        response = self.client.post(
            "/api/common/access-grants/bulk_update/",
            {
                "grants": [
                    {
                        "role": "CASHIER",
                        "module": "general_ledger",
                        "function_type": "MAINTENANCE",
                        "is_allowed": True,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 207)
        self.assertEqual(len(response.data["missing"]), 1)
