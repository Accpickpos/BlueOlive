"""
Management command to fix the pos_jobcard.status column in all shop schemas.
This runs SQL directly without going through Django migrations.
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix the pos_jobcard.status column to varchar(25) in all schemas'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # List all schemas
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'pg_toast', 'information_schema')
            AND schema_name NOT LIKE 'pg_temp%'
            ORDER BY schema_name
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        self.stdout.write(f"Found schemas: {schemas}")
        
        fixed_count = 0
        for schema in schemas:
            self.stdout.write(f"\n=== Checking schema: {schema} ===")
            
            try:
                # Check if pos_jobcard table exists in this schema
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = '{schema}' 
                        AND table_name = 'pos_jobcard'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(f"  pos_jobcard table does not exist in schema {schema}")
                    continue
                    
                # Check current status column definition
                cursor.execute(f"""
                    SELECT column_name, data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_schema = '{schema}' 
                    AND table_name = 'pos_jobcard' 
                    AND column_name = 'status'
                """)
                result = cursor.fetchone()
                
                if not result:
                    self.stdout.write(self.style.ERROR(f"  status column not found in schema {schema}"))
                    continue
                
                column_name, data_type, max_length = result
                self.stdout.write(f"  Current: {column_name} {data_type}({max_length})")
                
                if max_length and max_length < 25:
                    self.stdout.write(self.style.WARNING(f"  Column is varchar({max_length}), needs to be varchar(25)"))
                    
                    try:
                        # Attempt the ALTER
                        cursor.execute(f'ALTER TABLE "{schema}".pos_jobcard ALTER COLUMN status TYPE varchar(25)')
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Fixed schema {schema}"))
                        fixed_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ Error: {e}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Already correct"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing schema {schema}: {e}"))
        
        self.stdout.write(f"\n=== Summary ===")
        self.stdout.write(f"Fixed {fixed_count} schema(s)")
