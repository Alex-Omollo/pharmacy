#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from core.models import User, Role

print("🔧 Fixing admin user roles...\n")

admin_role = Role.objects.get(name='admin')

# Get all superusers
superusers = User.objects.filter(is_superuser=True)

for user in superusers:
    old_role = user.role.name if user.role else 'No Role'
    user.role = admin_role
    user.save()
    print(f"✅ {user.username}: {old_role} → admin")

print("\n✅ Done!")
