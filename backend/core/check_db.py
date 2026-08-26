#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection  # noqa: E402

cursor = connection.cursor()
cursor.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'pos_%'"
)
tables = cursor.fetchall()
print("POS tables found:")
for t in tables:
    print(f"  - {t[0]}")

# Check jobcard columns
cursor.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_jobcard'"
)
cols = cursor.fetchall()
print("\npos_jobcard columns:")
for c in cols:
    print(f"  - {c[0]}")

# Check if debtor_account_number exists
cursor.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_jobcard' AND column_name = 'debtor_account_number'"
)
result = cursor.fetchall()
print(f"\ndebtor_account_number exists: {len(result) > 0}")
