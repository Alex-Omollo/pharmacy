#!/usr/bin/env python
"""
Check and fix JWT response issue
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from core.models import User, Role
from rest_framework_simplejwt.tokens import RefreshToken

def test_jwt_response():
    print("🔍 Testing JWT response...")
    
    # Get admin user
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ Admin user not found!")
        return
    
    print(f"\n👤 User: {admin.username}")
    print(f"📧 Email: {admin.email}")
    print(f"🎭 Role object: {admin.role}")
    
    if admin.role:
        print(f"✅ Role name: {admin.role.name}")
        print(f"✅ Role display: {admin.role.get_name_display()}")
    else:
        print("❌ NO ROLE ASSIGNED!")
        print("\n🔧 Fixing role...")
        admin_role = Role.objects.get(name='admin')
        admin.role = admin_role
        admin.save()
        print("✅ Role assigned!")
    
    # Test token generation
    print("\n🔑 Generating test tokens...")
    refresh = RefreshToken.for_user(admin)
    
    print(f"✅ Refresh token: {str(refresh)[:50]}...")
    print(f"✅ Access token: {str(refresh.access_token)[:50]}...")
    
    # Simulate the custom serializer response
    user_data = {
        'id': admin.id,
        'username': admin.username,
        'email': admin.email,
        'first_name': admin.first_name,
        'last_name': admin.last_name,
        'role': admin.role.name if admin.role else None,
        'role_display': admin.role.get_name_display() if admin.role else None,
    }
    
    print("\n📦 User data that should be returned:")
    import json
    print(json.dumps(user_data, indent=2))
    
    if user_data['role'] is None:
        print("\n❌ PROBLEM: Role is None!")
    else:
        print(f"\n✅ Everything looks good! Role: {user_data['role']}")

if __name__ == '__main__':
    test_jwt_response()