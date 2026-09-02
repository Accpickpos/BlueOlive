# Generated migration to create AuditLog table

from django.db import migrations


def create_auditlog_table(apps, schema_editor):
    """Create the AuditLog table manually"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenancy_auditlog (
                id BIGSERIAL PRIMARY KEY,
                action VARCHAR(20) NOT NULL,
                resource_type VARCHAR(50) NOT NULL DEFAULT '',
                resource_id VARCHAR(100) NOT NULL DEFAULT '',
                ip_address INET,
                user_agent TEXT NOT NULL DEFAULT '',
                tenant_id INT,
                details JSONB NOT NULL DEFAULT '{}',
                success BOOLEAN NOT NULL DEFAULT TRUE,
                error_message TEXT NOT NULL DEFAULT '',
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id INT
            );
            
            CREATE INDEX IF NOT EXISTS tenancy_aud_timesta_02256b_idx ON tenancy_auditlog(timestamp);
            CREATE INDEX IF NOT EXISTS tenancy_aud_user_id_bbdc4b_idx ON tenancy_auditlog(user_id, timestamp);
            CREATE INDEX IF NOT EXISTS tenancy_aud_action_ff4aee_idx ON tenancy_auditlog(action, timestamp);
            CREATE INDEX IF NOT EXISTS tenancy_aud_tenant__324d97_idx ON tenancy_auditlog(tenant_id, timestamp);
        """)


def drop_auditlog_table(apps, schema_editor):
    """Drop the AuditLog table"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS tenancy_auditlog CASCADE")


class Migration(migrations.Migration):

    dependencies = [
        ("tenancy", "0004_auditlog"),
    ]

    operations = [
        migrations.RunPython(create_auditlog_table, drop_auditlog_table),
    ]
