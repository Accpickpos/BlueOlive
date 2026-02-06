#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

print("Databases configured:")
for db_alias, db_config in settings.DATABASES.items():
    print(f"  {db_alias}: {db_config.get('NAME')}")
