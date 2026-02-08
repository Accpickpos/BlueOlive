import os
from pathlib import Path

# Find Django admin migrations in site-packages
venv_path = Path('.venv/Lib/site-packages/django/contrib/admin/migrations')
if venv_path.exists():
    migration_file = venv_path / '0001_initial.py'
    if migration_file.exists():
        with open(migration_file) as f:
            content = f.read()
            # Look for references to User
            if 'User' in content or 'user' in content:
                print('Admin migration references user/User:')
                for i, line in enumerate(content.split('\n'), 1):
                    if ('User' in line or 'user' in line) and i < 100:
                        print(f'  {line.strip()[:80]}')
    else:
        print("Migration file not found")
else:
    print("Admin migrations directory not found")
