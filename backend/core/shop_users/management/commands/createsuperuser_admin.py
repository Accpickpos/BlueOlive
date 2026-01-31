"""
Management command to create admin superusers for managing tenants.
These users are stored in the DEFAULT database, not tenant databases.

Usage:
    python manage.py createsuperuser_admin
    python manage.py createsuperuser_admin --username=admin --email=admin@example.com
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create an admin superuser for managing tenants'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the admin')
        parser.add_argument('--email', type=str, help='Email for the admin')
        parser.add_argument('--password', type=str, help='Password for the admin')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')

        # Prompt for missing fields
        if not username:
            username = input('Username: ')
        if not email:
            email = input('Email: ')
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match.'))
                return

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists.')
            )
            return

        # Create the superuser
        try:
            User.objects.create_superuser(username, email, password)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Admin superuser "{username}" created successfully!\n'
                    f'Email: {email}\n'
                    f'Login at: http://localhost:8000/admin'
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))
