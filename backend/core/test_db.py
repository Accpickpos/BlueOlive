#!/usr/bin/env python
import os
import sys

# Add the path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

# Check all database configs
output = []
output.append("DATABASES:")
for name, config in settings.DATABASES.items():
    output.append(f"{name}:")
    output.append(f'  NAME: {config.get("NAME", "N/A")}')
    output.append(f'  HOST: {config.get("HOST", "N/A")}')
    output.append(f'  PORT: {config.get("PORT", "N/A")}')

# Write to file
with open("db_config.txt", "w") as f:
    f.write("\n".join(output))

print("Written to db_config.txt")
