#!/usr/bin/env python
"""Manually create debtors tables using Django's schema editor."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.db.backends.postgresql.schema import DatabaseSchemaEditor
from apps.debtors import models as debtors_models

alias = 'tenant_1'
conn = connections[alias]

# Get all models from the debtors app
models_to_create = [
    debtors_models.Debtor, debtors_models.AuditLog, debtors_models.DebtorTransaction,
    debtors_models.Invoice, debtors_models.InvoiceLine, debtors_models.PostDatedCheque,
    debtors_models.Darea, debtors_models.Dpdc, debtors_models.Debtopen, debtors_models.DebtorAudit,
    debtors_models.SalesOrder, debtors_models.SalesOrderLine, debtors_models.JobCosting,
    debtors_models.JobCostingTransaction, debtors_models.JobPerson, debtors_models.JobPrinting
]

print(f"Creating tables in {alias} database...")

with DatabaseSchemaEditor(conn) as schema_editor:
    for model in models_to_create:
        try:
            schema_editor.create_model(model)
            print(f"✓ Created {model._meta.db_table}")
        except Exception as e:
            print(f"✗ {model._meta.db_table}: {str(e)[:100]}")

print("\n✓ Tables created successfully!")
