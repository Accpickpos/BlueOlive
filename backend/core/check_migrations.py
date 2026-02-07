import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.db.migrations.loader import MigrationLoader

# Load migrations from Django
loader = MigrationLoader(None)

# Check auth migrations
auth_migrations = loader.disk_migrations.get('auth', {})
print('Auth migrations on disk:')
for key in sorted(auth_migrations.keys()):
    print(f'  {key}')

# Check sessions migrations
sessions_migrations = loader.disk_migrations.get('sessions', {})
print('\nSessions migrations on disk:')
for key in sorted(sessions_migrations.keys()):
    print(f'  {key}')
