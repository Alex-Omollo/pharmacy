#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from core.models import User, Role

print("🔧 Complete POS Setup\n")

# Step 1: Initialize Roles
print("1️⃣ Initializing roles...")
roles_data = [
    {'name': 'admin', 'description': 'Full system access'},
    {'name': 'manager', 'description': 'Manager access'},
    {'name': 'cashier', 'description': 'Cashier access'},
]

for role_data in roles_data:
    role, created = Role.objects.get_or_create(
        name=role_data['name'],
        defaults={'description': role_data['description']}
    )
    status = "created" if created else "exists"
    print(f"   ✓ {role.name} ({status})")

# Step 2: Create/Fix Users
print("\n2️⃣ Setting up users...")
admin_role = Role.objects.get(name='admin')
manager_role = Role.objects.get(name='manager')
cashier_role = Role.objects.get(name='cashier')

users_data = [
    {
        'username': 'admin',
        'email': 'admin@pos.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': admin_role,
        'is_superuser': True,
        'is_staff': True,
    },
    {
        'username': 'manager',
        'email': 'manager@pos.com',
        'password': 'manager123',
        'first_name': 'Manager',
        'last_name': 'User',
        'role': manager_role,
    },
    {
        'username': 'cashier',
        'email': 'cashier@pos.com',
        'password': 'cashier123',
        'first_name': 'Cashier',
        'last_name': 'User',
        'role': cashier_role,
    },
]

for user_data in users_data:
    password = user_data.pop('password')
    username = user_data['username']
    
    user, created = User.objects.update_or_create(
        username=username,
        defaults=user_data
    )
    user.set_password(password)
    user.save()
    
    status = "created" if created else "updated"
    print(f"   ✓ {username} ({status}) - role: {user.role.name}")

# Step 3: Verify
print("\n3️⃣ Verification...")
for username in ['admin', 'manager', 'cashier']:
    user = User.objects.get(username=username)
    print(f"   ✓ {username}: role={user.role.name}, is_admin={user.is_admin}")

print("\n✅ Setup complete!\n")
print("Login credentials:")
print("  Admin    - username: admin    password: admin123")
print("  Manager  - username: manager  password: manager123")
print("  Cashier  - username: cashier  password: cashier123")