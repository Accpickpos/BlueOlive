"""
Regression tests for the legacy CSV import pipeline (import_views.py).

Run with: python manage.py test apps.saas_admin
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import psycopg2
from apps.debtors.models import Debtopen, Debtor, DebtorAudit, DebtorTransaction
from apps.saas_admin.import_views import (
    _import_debtoaud_record,
    _import_debtopen_record,
    _import_debtor_record,
    _import_debtran_record,
    _import_department_record,
    _uoc,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections
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


class DebtorImportPipelineTestCase(SimpleTestCase):
    """
    Regression tests for three compounding bugs in the debtor-transaction
    import path (debtran/debtopen/debtoaud), found while auditing whether
    DebtorOpenItem could be deleted as unused:

    1. _import_debtran_record wrote into DebtorOpenItem instead of
       DebtorTransaction (copy-paste from _import_debtopen_record).
    2. _import_debtopen_record's target, DebtorOpenItem, maps to a
       different physical table ("debtopen") than the one the live app
       reads (Debtopen, table "debtors_debtopen") — imported data landed
       somewhere the app could never show a user.
    3. _uoc's _resolve_fields assumed Django's default column-naming
       convention (FK field -> "{field}_id"), which is wrong for several
       of these models' explicit db_column overrides (e.g. DebtorAudit.dno
       -> db_column="dno", not "dno_id"), and DEBTOPEN_CSV_TO_MODEL_FIELD_MAP/
       DEBTOAUD_CSV_TO_MODEL_FIELD_MAP targeted field names that don't
       exist on the real models at all.

    Creates real Debtor/DebtorTransaction/Debtopen/DebtorAudit tables (via
    Django's own schema editor, so the structure is identical to what a
    real migration produces) in a throwaway schema, then exercises the
    actual _import_*_record functions end-to-end through _uoc's raw-psycopg2
    path — the one real imports actually use.
    """

    # Needed because setUpClass uses Django's own connections["default"]
    # (via DatabaseSchemaEditor) in addition to the raw psycopg2 connection
    # _uoc itself uses — SimpleTestCase forbids ORM DB access by default.
    databases = {"default"}

    SCHEMA = "test_debtor_import_schema"

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
                # TimeStampedModel's created_by/updated_by FKs point at
                # AUTH_USER_MODEL (shop_users.ShopUser) — create a minimal
                # placeholder so those deferred FK constraints have
                # something to reference; this test never populates either
                # field, so an id-only stand-in is enough.
                cur.execute(
                    f"CREATE TABLE {cls.SCHEMA}.shop_users_shopuser "
                    f"(id BIGSERIAL PRIMARY KEY)"
                )
        finally:
            conn.close()

        # Create the real model tables via Django's own schema editor, so
        # the structure (including every db_column override) is identical
        # to what `migrate` would produce — not a hand-maintained copy that
        # could drift from the model.
        from django.db.backends.postgresql.schema import DatabaseSchemaEditor

        django_conn = connections["default"]
        django_conn.close()
        django_conn.connect()
        with django_conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{cls.SCHEMA}", public')
        django_conn.commit()

        with DatabaseSchemaEditor(django_conn) as schema_editor:
            for model in (Debtor, DebtorTransaction, Debtopen, DebtorAudit):
                with django_conn.cursor() as cur:
                    cur.execute(f'SET search_path TO "{cls.SCHEMA}", public')
                schema_editor.create_model(model)
        django_conn.commit()
        django_conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = cls._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {cls.SCHEMA} CASCADE")
        finally:
            conn.close()
        super().tearDownClass()

    def setUp(self):
        # _resolve_debtor (called by every _import_*_record fixed by this
        # change) looks the debtor up via the regular Django ORM connection
        # — unlike _uoc's raw-psycopg2 path, that connection's search_path
        # isn't self-contained, so it must be pointed at the test schema
        # for every test method, not just once in setUpClass.
        django_conn = connections["default"]
        django_conn.close()
        django_conn.connect()
        with django_conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{self.SCHEMA}", public')
        django_conn.commit()

        # A debtor row every test's FK lookups resolve against. Shared
        # across test methods in this class (no per-test truncation), so
        # this is idempotent create-or-update, not necessarily "created".
        result = _import_debtor_record(
            "default",
            {"dno": 5001, "dname": "Import Pipeline Test Debtor"},
            "create_or_update",
            schema_name=self.SCHEMA,
        )
        self.assertIn(result, ("created", "updated"))
        # FK columns on DebtorTransaction/Debtopen/DebtorAudit store the
        # Debtor row's actual primary key (standard Django FK behavior) —
        # not the business-meaningful "dno" value, even though several of
        # those columns are also (confusingly) *named* "dno" via
        # db_column. Tests below compare against this, not against 5001.
        self.debtor_pk = Debtor.objects.using("default").get(dno=5001).pk

    def _select_one(self, table, where_col, where_val):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{self.SCHEMA}", public')
                cur.execute(
                    f'SELECT * FROM "{table}" WHERE "{where_col}" = %s',  # nosec B608
                    [where_val],
                )
                columns = [d[0] for d in cur.description]
                row = cur.fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(
            row, f"No row found in {table} where {where_col}={where_val}"
        )
        return dict(zip(columns, row))

    def test_debtran_writes_to_debtor_transaction_not_debtor_open_item(self):
        result = _import_debtran_record(
            "default",
            {
                "debtor": 5001,
                "transaction_number": "000001",
                "transaction_date": "2026-01-15",
                "transaction_type": "IN",
                "subtotal": "100.00",
                "total_amount": "115.00",
            },
            "create_or_update",
            schema_name=self.SCHEMA,
        )
        self.assertEqual(result, "created")

        row = self._select_one("debtran", "dtrano", "000001")
        # DebtorTransaction.debtor has an explicit db_column="dno" override
        # (no "_id" suffix) — unlike Debtopen.dno below, which has none.
        self.assertEqual(row["dno"], self.debtor_pk)
        self.assertEqual(str(row["dtsub"]), "100.00")
        self.assertEqual(str(row["dttot"]), "115.00")

    def test_debtopen_writes_to_debtopen_table_debtopen_model(self):
        result = _import_debtopen_record(
            "default",
            {
                "dno": 5001,
                "dtrano": "000002",
                "type": "IN",
                "date": "2026-01-15",
                "total": "115.00",
                "balancedue": "115.00",
            },
            "create_or_update",
            schema_name=self.SCHEMA,
        )
        self.assertEqual(result, "created")

        row = self._select_one("debtors_debtopen", "dtrano", "000002")
        self.assertEqual(row["dno_id"], self.debtor_pk)
        self.assertEqual(str(row["total"]), "115.00")
        self.assertEqual(str(row["balancedue"]), "115.00")

    def test_debtoaud_writes_real_field_names_not_fictional_ones(self):
        result = _import_debtoaud_record(
            "default",
            {
                "dno": 5001,
                "dtrano": "000003",
                "type": "IN",
                "thistype": "IN",
                "thistran": "000003",
                "date": "2026-01-15",
                "amount": "115.00",
            },
            "create_or_update",
            schema_name=self.SCHEMA,
        )
        self.assertEqual(result, "created")

        row = self._select_one("debtoraud", "dtrano", "000003")
        # DebtorAudit.dno also has an explicit db_column="dno" override.
        self.assertEqual(row["dno"], self.debtor_pk)
        self.assertEqual(row["thistype"], "IN")
        self.assertEqual(row["thistran"], "000003")
        self.assertEqual(str(row["amount"]), "115.00")


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
            {
                "user_id": self.target_user.id,
                "new_password": "hacked-password-123",
            },  # nosec B105
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
            {
                "user_id": self.target_user.id,
                "new_password": "new-password-456",
            },  # nosec B105
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.check_password("new-password-456"))
