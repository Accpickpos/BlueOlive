"""
Regression tests for the legacy CSV import pipeline (import_views.py).

Run with: python manage.py test apps.saas_admin
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import psycopg2
from apps.saas_admin.import_views import _import_department_record, _uoc
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class ImportDepartmentRecordTestCase(SimpleTestCase):
    """
    Regression test for: importing department number 0 raised a downstream
    ForeignKeyViolation ('department_id=0 not present in sales_departments')
    on the FIRST stock item referencing it. Root cause: `if not dept_number:`
    treated the legitimate department number 0 the same as a missing value
    and silently skipped creating it, so nothing ever resolved dept 0 for
    later imports. (The other half of this bug - _uoc's _apply_not_null_defaults
    fabricating department_id=0 for any unresolved required FK - is covered
    by UocNotNullForeignKeyTestCase below.)
    """

    @patch("apps.saas_admin.import_views._uoc")
    @patch("apps.saas_admin.import_views.SalesDepartment")
    def test_department_number_zero_is_not_skipped(self, mock_dept_model, mock_uoc):
        mock_dept_model.objects.using.return_value = MagicMock()
        mock_uoc.return_value = "created"

        result = _import_department_record(
            "default",
            {"number": 0},
            "create_or_update",
            schema_name="irrelevant",
        )

        mock_uoc.assert_called_once()
        called_lookup = mock_uoc.call_args[0][1]
        self.assertEqual(called_lookup, {"number": 0})
        self.assertEqual(result, "created")

    @patch("apps.saas_admin.import_views._uoc")
    @patch("apps.saas_admin.import_views.SalesDepartment")
    def test_missing_department_number_is_still_skipped(
        self, mock_dept_model, mock_uoc
    ):
        result = _import_department_record(
            "default",
            {"number": None},
            "create_or_update",
            schema_name="irrelevant",
        )
        mock_uoc.assert_not_called()
        self.assertEqual(result, "skipped")


class UocNotNullForeignKeyTestCase(SimpleTestCase):
    """
    Regression test for: _uoc()'s _apply_not_null_defaults() filled ANY
    missing NOT NULL integer column with a fabricated 0 - including foreign
    key columns. For stock_items.department_id (NOT NULL, no default), an
    unresolved department produced a literal `department_id=0` INSERT,
    which either violates the FK constraint (as reported: 'Key
    (department_id)=(0) is not present in table "sales_departments"') or,
    worse, would silently succeed if some unrelated row 0 ever existed.

    Uses a throwaway schema on the real 'default' Postgres database via raw
    psycopg2 (bypassing Django's ORM/test-transaction wrapping entirely,
    since _uoc's schema_name path does the same) so setup/teardown and _uoc's
    own connection see the same committed state.
    """

    SCHEMA = "test_uoc_fk_schema"

    @classmethod
    def _connect(cls):
        db = settings.DATABASES["default"]
        conn = psycopg2.connect(
            dbname=db["NAME"],
            user=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=int(db["PORT"]),
        )
        conn.autocommit = True
        return conn

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        conn = cls._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {cls.SCHEMA} CASCADE")
                cur.execute(f"CREATE SCHEMA {cls.SCHEMA}")
                cur.execute(f"""
                    CREATE TABLE {cls.SCHEMA}.parent_dept (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL
                    )
                """)
                cur.execute(f"""
                    CREATE TABLE {cls.SCHEMA}.child_item (
                        id SERIAL PRIMARY KEY,
                        stock_code VARCHAR(20) NOT NULL,
                        department_id INTEGER NOT NULL
                            REFERENCES {cls.SCHEMA}.parent_dept(id),
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                """)
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = cls._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {cls.SCHEMA} CASCADE")
        finally:
            conn.close()
        super().tearDownClass()

    def tearDown(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"TRUNCATE {self.SCHEMA}.child_item, {self.SCHEMA}.parent_dept RESTART IDENTITY CASCADE"
                )
        finally:
            conn.close()

    def _manager(self, table_name):
        return SimpleNamespace(
            db="default",
            model=SimpleNamespace(_meta=SimpleNamespace(db_table=table_name)),
        )

    def test_missing_required_fk_raises_not_null_not_fabricated_fk(self):
        # _uoc uses a raw psycopg2 connection (not Django's), so the error
        # surfaces as psycopg2's own exception type, not Django's IntegrityError.
        with self.assertRaises(psycopg2.errors.NotNullViolation) as ctx:
            _uoc(
                self._manager("child_item"),
                {"stock_code": "SC001"},
                {},  # department_id deliberately omitted - unresolved FK
                "create_or_update",
                schema_name=self.SCHEMA,
            )

        # Must fail as a NOT NULL violation naming department_id - NOT a
        # ForeignKeyViolation from a fabricated department_id=0.
        message = str(ctx.exception).lower()
        self.assertIn("department_id", message)
        self.assertIn("null", message)

    def test_resolved_fk_still_inserts_correctly(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # self.SCHEMA is the hardcoded test-class constant above.
                cur.execute(
                    f"INSERT INTO {self.SCHEMA}.parent_dept (name) VALUES ('Zero Dept') RETURNING id"  # nosec B608
                )
                dept_id = cur.fetchone()[0]
        finally:
            conn.close()

        result = _uoc(
            self._manager("child_item"),
            {"stock_code": "SC002"},
            {"department_id": dept_id},
            "create_or_update",
            schema_name=self.SCHEMA,
        )
        self.assertEqual(result, "created")

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # self.SCHEMA is the hardcoded test-class constant above.
                cur.execute(
                    f"SELECT department_id FROM {self.SCHEMA}.child_item WHERE stock_code = 'SC002'"  # nosec B608
                )
                row = cur.fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], dept_id)


# ============================================================
# Access-control regression tests
#
# Confirmed critical finding: every endpoint in this app used DRF's stock
# `rest_framework.permissions.IsAdminUser`, which only checks
# `request.user.is_staff`. ShopUser.save() (shop_users/models.py) sets
# `is_staff = role in ("ADMIN", "MANAGER", "STAFF")` for ANY tenant
# employee above cashier level, so any regular tenant staff member — from
# any tenant — could reach this "superuser only" cross-tenant admin app.
# Fixed by apps.saas_admin.permissions.IsPlatformSuperuser, which checks
# the real `request.user.is_superuser` flag instead. These tests lock in
# that a merely-is_staff tenant user is rejected and a real superuser is
# allowed.
# ============================================================

User = get_user_model()


class PlatformAdminAccessControlTestCase(APITestCase):
    """
    Regression tests for the IsAdminUser -> IsPlatformSuperuser fix.

    tenant_id on ShopUser is a plain IntegerField (no FK constraint - see
    shop_users/models.py), so these tests use arbitrary tenant_id values
    without needing real Tenant rows.
    """

    TENANT_STAFF_PASSWORD = "tenant-staff-pass-123"  # nosec B105 - test fixture
    SUPERUSER_PASSWORD = "platform-super-pass-123"  # nosec B105 - test fixture
    TARGET_PASSWORD = "old-password-123"  # nosec B105 - test fixture

    def setUp(self):
        self.client = APIClient()

        # A regular tenant employee: is_staff=True (via role), but NOT a
        # real Django superuser. This is exactly the account type the bug
        # let through.
        self.tenant_staff = User.objects.create_user(
            username="tenant_staff_user",
            email="tenant_staff@example.com",
            password=self.TENANT_STAFF_PASSWORD,
            tenant_id=4242,
            role="STAFF",
        )
        self.assertTrue(self.tenant_staff.is_staff)
        self.assertFalse(self.tenant_staff.is_superuser)

        # A real platform superuser (as created by createsuperuser_admin).
        self.superuser = User.objects.create_superuser(
            username="platform_superuser",
            email="platform_admin@example.com",
            password=self.SUPERUSER_PASSWORD,
        )
        self.assertTrue(self.superuser.is_superuser)

        # A target user whose password the superuser will reset.
        self.target_user = User.objects.create_user(
            username="target_user",
            email="target_user@example.com",
            password=self.TARGET_PASSWORD,
            tenant_id=4242,
            role="CASHIER",
        )

    def test_tenant_staff_cannot_list_tenants(self):
        """Non-superuser tenant staff must not reach the tenant list endpoint."""
        self.client.force_authenticate(user=self.tenant_staff)
        response = self.client.get("/api/v1/saas-admin/tenants/")
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_tenant_staff_cannot_reset_password(self):
        """Non-superuser tenant staff must not reach the reset-password endpoint."""
        self.client.force_authenticate(user=self.tenant_staff)
        response = self.client.post(
            "/api/v1/saas-admin/users/reset-password/",
            {"user_id": self.target_user.id, "new_password": "hacked-password-123"},
        )
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
        # Confirm the password was NOT actually changed.
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password(self.TARGET_PASSWORD))

    def test_superuser_can_list_tenants(self):
        """A real platform superuser must be able to reach the tenant list endpoint."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get("/api/v1/saas-admin/tenants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_superuser_can_reset_password(self):
        """A real platform superuser must be able to reset another user's password."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            "/api/v1/saas-admin/users/reset-password/",
            {"user_id": self.target_user.id, "new_password": "new-password-456"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password("new-password-456"))
