"""
Management command to check and fix the pos_jobcard.status column in shop schema.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Check and fix the pos_jobcard.status column definition in shop schema"

    def handle(self, *args, **options):
        cursor = connection.cursor()

        # First, list all schemas to find shop schemas
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'pg_toast', 'information_schema')
            AND schema_name NOT LIKE 'pg_temp%'
            ORDER BY schema_name
        """)

        schemas = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f"Found schemas: {schemas}")

        # Check each schema for pos_jobcard table
        for schema in schemas:
            try:
                # `schema` is read back from information_schema.schemata above,
                # not external input - dev diagnostic command, not a web view.
                query = f"""
                    SELECT column_name, data_type, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = '{schema}'
                    AND table_name = 'pos_jobcard'
                    AND column_name = 'status'
                """
                cursor.execute(query)  # nosec B608
                result = cursor.fetchone()

                if result:
                    self.stdout.write(f"\n=== Schema: {schema} ===")
                    self.stdout.write(f"Column: {result[0]}")
                    self.stdout.write(f"Type: {result[1]}")
                    self.stdout.write(f"Max Length: {result[2]}")

                    if result[2] and result[2] < 25:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Column max_length is {result[2]}, expected 25"
                            )
                        )
                        self.stdout.write("Attempting to fix...")

                        try:
                            cursor.execute(f"""
                                ALTER TABLE "{schema}".pos_jobcard ALTER COLUMN status TYPE varchar(25)
                            """)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Successfully altered column to varchar(25)"
                                )
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"Error altering column: {e}")
                            )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS("Column definition is correct")
                        )

                    # Also list all columns
                    # `schema` is read back from information_schema.schemata
                    # above, not external input.
                    query = f"""
                        SELECT column_name, data_type, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_schema = '{schema}'
                        AND table_name = 'pos_jobcard'
                        AND data_type = 'character varying'
                        ORDER BY column_name
                    """
                    cursor.execute(query)  # nosec B608
                    self.stdout.write("\nAll varchar columns in pos_jobcard:")
                    for row in cursor.fetchall():
                        self.stdout.write(f"  {row[0]}: varchar({row[2]})")

            except Exception as e:
                self.stdout.write(f"\n=== Schema: {schema} ===")
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
