#!/usr/bin/env python
"""
Check RefreshToken API and see if we can specify database.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import inspect
from rest_framework_simplejwt.tokens import RefreshToken

# Check the signature of for_user
sig = inspect.signature(RefreshToken.for_user)
print(f"RefreshToken.for_user signature: {sig}")

# Check the source
print(f"\nRefreshToken.for_user source:")
print(inspect.getsource(RefreshToken.for_user))
