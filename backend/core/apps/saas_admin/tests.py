"""
Regression tests for the legacy CSV import pipeline (import_views.py).

Run with: python manage.py test apps.saas_admin
"""
import psycopg2
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from django.conf import settings
from django.test import SimpleTestCase

from apps.saas_admin.import_views import _import_department_record, _uoc


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

    @patch('apps.saas_admin.import_views._uoc')
    @patch('apps.saas_admin.import_views.SalesDepartment')
    def test_department_number_zero_is_not_skipped(self, mock_dept_model, mock_uoc):
        mock_dept_model.objects.using.return_value = MagicMock()
        mock_uoc.return_value = 'created'

        result = _import_department_record(
            'default', {'number': 0}, 'create_or_update', schema_name='irrelevant',
        )

        mock_uoc.assert_called_once()
        called_lookup = mock_uoc.call_args[0][1]
        self.assertEqual(called_lookup, {'number': 0})
        self.assertEqual(result, 'created')

    @patch('apps.saas_admin.import_views._uoc')
    @patch('apps.saas_admin.import_views.SalesDepartment')
    def test_missing_department_number_is_still_skipped(self, mock_dept_model, mock_uoc):
        result = _import_department_record(
            'default', {'number': None}, 'create_or_update', schema_name='irrelevant',
        )
        mock_uoc.assert_not_called()
        self.assertEqual(result, 'skipped')


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

    SCHEMA = 'test_uoc_fk_schema'

    @classmethod
    def _connect(cls):
        db = settings.DATABASES['default']
        conn = psycopg2.connect(
            dbname=db['NAME'], user=db['USER'], password=db['PASSWORD'],
            host=db['HOST'], port=int(db['PORT']),
        )
        conn.autocommit = True
        return conn

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        conn = cls._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS {cls.SCHEMA} CASCADE')
                cur.execute(f'CREATE SCHEMA {cls.SCHEMA}')
                cur.execute(f'''
                    CREATE TABLE {cls.SCHEMA}.parent_dept (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL
                    )
                ''')
                cur.execute(f'''
                    CREATE TABLE {cls.SCHEMA}.child_item (
                        id SERIAL PRIMARY KEY,
                        stock_code VARCHAR(20) NOT NULL,
                        department_id INTEGER NOT NULL
                            REFERENCES {cls.SCHEMA}.parent_dept(id),
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
        finally:
            conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = cls._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS {cls.SCHEMA} CASCADE')
        finally:
            conn.close()
        super().tearDownClass()

    def tearDown(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f'TRUNCATE {self.SCHEMA}.child_item, {self.SCHEMA}.parent_dept RESTART IDENTITY CASCADE'
                )
        finally:
            conn.close()

    def _manager(self, table_name):
        return SimpleNamespace(
            db='default',
            model=SimpleNamespace(_meta=SimpleNamespace(db_table=table_name)),
        )

    def test_missing_required_fk_raises_not_null_not_fabricated_fk(self):
        # _uoc uses a raw psycopg2 connection (not Django's), so the error
        # surfaces as psycopg2's own exception type, not Django's IntegrityError.
        with self.assertRaises(psycopg2.errors.NotNullViolation) as ctx:
            _uoc(
                self._manager('child_item'),
                {'stock_code': 'SC001'},
                {},  # department_id deliberately omitted - unresolved FK
                'create_or_update',
                schema_name=self.SCHEMA,
            )

        # Must fail as a NOT NULL violation naming department_id - NOT a
        # ForeignKeyViolation from a fabricated department_id=0.
        message = str(ctx.exception).lower()
        self.assertIn('department_id', message)
        self.assertIn('null', message)

    def test_resolved_fk_still_inserts_correctly(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {self.SCHEMA}.parent_dept (name) VALUES ('Zero Dept') RETURNING id"
                )
                dept_id = cur.fetchone()[0]
        finally:
            conn.close()

        result = _uoc(
            self._manager('child_item'),
            {'stock_code': 'SC002'},
            {'department_id': dept_id},
            'create_or_update',
            schema_name=self.SCHEMA,
        )
        self.assertEqual(result, 'created')

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT department_id FROM {self.SCHEMA}.child_item WHERE stock_code = 'SC002'"
                )
                row = cur.fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], dept_id)
