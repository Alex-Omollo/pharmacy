#!/usr/bin/env python
"""
Initial Admin Setup Script
Run this ONCE when deploying the application for the first time
Creates two admin users with default passwords that should be changed after first login
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from core.models import User, Role
from django.db import transaction


# 🔑 DEFAULT CREDENTIALS - Change after first login!
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'admin123'  # User should change this after first login
DEFAULT_ADMIN_EMAIL = 'admin@feedshub.co.ke'

DEFAULT_SUPERADMIN_USERNAME = 'superadmin'
DEFAULT_SUPERADMIN_PASSWORD = '4fu(ax(Iy78W'  # Strong default password
DEFAULT_SUPERADMIN_EMAIL = 'superadmin@feedshub.internal'


def setup_initial_admins():
    """Setup initial admin users for the system"""
    
    print("\n" + "="*70)
    print("🔐 FeedsHub POS - Initial Admin Setup")
    print("="*70 + "\n")
    
    # Ensure admin role exists
    try:
        admin_role = Role.objects.get(name='admin')
    except Role.DoesNotExist:
        print("❌ Admin role not found. Creating roles...")
        admin_role = Role.objects.create(
            name='admin',
            description='Full system access'
        )
        Role.objects.create(name='manager', description='Manager access')
        Role.objects.create(name='cashier', description='Cashier access')
        print("✅ Roles created\n")
    
    with transaction.atomic():
        # 1. Create Main Admin User
        print("📋 MAIN ADMIN SETUP")
        print("-" * 70)
        
        main_admin_exists = User.objects.filter(username=DEFAULT_ADMIN_USERNAME).exists()
        
        if main_admin_exists:
            print(f"⚠️  Main admin user '{DEFAULT_ADMIN_USERNAME}' already exists.")
            print("   Password reset skipped. Use password reset feature if needed.\n")
        else:
            print(f"Creating new main admin user: {DEFAULT_ADMIN_USERNAME}")
            
            User.objects.create_user(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                first_name='System',
                last_name='Administrator',
                role=admin_role,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print("✅ Main admin user created!\n")
        
        # 2. Create Hidden Super Admin (Emergency Access)
        print("🔒 HIDDEN SUPER ADMIN SETUP")
        print("-" * 70)
        print("This is a hidden emergency admin account.")
        
        super_admin_exists = User.objects.filter(username=DEFAULT_SUPERADMIN_USERNAME).exists()
        
        if super_admin_exists:
            print(f"⚠️  Super admin user '{DEFAULT_SUPERADMIN_USERNAME}' already exists.")
            print("   Password reset skipped. Use password reset feature if needed.\n")
        else:
            print(f"Creating hidden super admin user: {DEFAULT_SUPERADMIN_USERNAME}")
            
            User.objects.create_user(
                username=DEFAULT_SUPERADMIN_USERNAME,
                email=DEFAULT_SUPERADMIN_EMAIL,
                password=DEFAULT_SUPERADMIN_PASSWORD,
                first_name='Super',
                last_name='Admin',
                role=admin_role,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print("✅ Super admin user created!\n")
    
    print("="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print("\n📝 DEFAULT LOGIN CREDENTIALS:\n")
    
    print("1️⃣  Main Admin Account:")
    print(f"   Username: {DEFAULT_ADMIN_USERNAME}")
    print(f"   Password: {DEFAULT_ADMIN_PASSWORD}")
    print("   Email:    " + DEFAULT_ADMIN_EMAIL)
    print("   Use for:  Regular administrative tasks\n")
    
    print("2️⃣  Super Admin Account (HIDDEN - Emergency Access):")
    print(f"   Username: {DEFAULT_SUPERADMIN_USERNAME}")
    print(f"   Password: {DEFAULT_SUPERADMIN_PASSWORD}")
    print("   Email:    " + DEFAULT_SUPERADMIN_EMAIL)
    print("   Use for:  Emergency access only\n")
    
    print("⚠️  IMPORTANT SECURITY NOTICE:")
    print("   1. Change these default passwords immediately after first login")
    print("   2. Store super admin credentials securely (password manager)")
    print("   3. Super admin account should only be used for emergencies")
    print("   4. Do not share super admin credentials with regular staff")
    print("="*70 + "\n")
    
    print("📌 How to change passwords:")
    print("   • Login to the system with the credentials above")
    print("   • Go to User Management → Change Password")
    print("   • Or use: POST /api/users/change-password/")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        setup_initial_admins()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error during setup: {str(e)}")