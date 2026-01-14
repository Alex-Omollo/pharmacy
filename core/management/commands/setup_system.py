"""
Django Management Command: setup_system
Complete system initialization - roles and admin account
Run this ONCE when setting up the system for the first time

Usage:
    python manage.py setup_system
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import User, Role


class Command(BaseCommand):
    help = 'Initialize system: Create roles and admin account'
    
    # 🔑 DEFAULT CREDENTIALS - Change after first login!
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin123'  # User can change this later
    DEFAULT_ADMIN_EMAIL = 'admin@feedshub.co.ke'
    DEFAULT_ADMIN_FIRST_NAME = 'System'
    DEFAULT_ADMIN_LAST_NAME = 'Administrator'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-admin',
            action='store_true',
            help='Only create roles, skip admin creation'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Custom admin username'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Custom admin password'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Custom admin email'
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🚀 FeedsHub POS - System Setup"))
        self.stdout.write("="*60 + "\n")

        # Step 1: Initialize Roles
        self._initialize_roles()
        
        # Step 2: Create Admin (unless skipped)
        if not options['skip_admin']:
            self._create_admin()
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("✅ SETUP COMPLETE!"))
        self.stdout.write("="*60 + "\n")

    def _initialize_roles(self):
        """Create system roles"""
        self.stdout.write("\n📋 Step 1: Initializing Roles...")
        self.stdout.write("-" * 60)
        
        roles_data = [
            {
                'name': Role.ADMIN,
                'description': 'Full system access - can manage users, products, sales, inventory, and reports'
            },
            {
                'name': Role.MANAGER,
                'description': 'Can manage products, inventory, view reports, and process sales'
            },
            {
                'name': Role.CASHIER,
                'description': 'Can only process sales transactions'
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✓ Created: {role.get_name_display()}")
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠ Exists: {role.get_name_display()}")
                )
                existing_count += 1
        
        self.stdout.write(
            f"\n   Summary: {created_count} created, {existing_count} already exist"
        )

    def _create_admin(self):
        """Automatically create admin using default credentials"""
        self.stdout.write("\n👤 Step 2: Admin Account Setup...")
        self.stdout.write("-" * 60)

        username = self.DEFAULT_ADMIN_USERNAME

        # Check if admin already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"   ⚠ Admin user '{username}' already exists. Skipping creation.")
            )
            return

        self._create_new_admin()


    def _reset_admin_password(self):
        """Reset password for existing admin user"""
        admin_user = User.objects.get(username='admin')
        
        self.stdout.write("\n   🔑 Set new password for admin:")
        
        while True:
            password = getpass.getpass("      Enter password: ")
            password2 = getpass.getpass("      Confirm password: ")
            
            if password != password2:
                self.stdout.write(
                    self.style.ERROR("      ❌ Passwords don't match. Try again.\n")
                )
                continue
            
            if len(password) < 8:
                self.stdout.write(
                    self.style.ERROR("      ❌ Password must be at least 8 characters. Try again.\n")
                )
                continue
            
            admin_user.set_password(password)
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS("   ✅ Admin password updated successfully!")
            )
            break

    def _create_new_admin(self):
        """Create a new admin user with default credentials"""
        self.stdout.write("   Creating new admin user...\n")

        # Get admin role
        try:
            admin_role = Role.objects.get(name=Role.ADMIN)
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("   ❌ Admin role not found. Please run role setup first.")
            )
            return

        # Use default credentials
        username = self.DEFAULT_ADMIN_USERNAME
        email = self.DEFAULT_ADMIN_EMAIL
        password = self.DEFAULT_ADMIN_PASSWORD
        first_name = self.DEFAULT_ADMIN_FIRST_NAME
        last_name = self.DEFAULT_ADMIN_LAST_NAME

        # Create admin user
        with transaction.atomic():
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=admin_role,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS("\n   ✅ Admin user created successfully!"))
        
        # Display credentials
        self.stdout.write("\n   📝 Admin Credentials (DEFAULT):")
        self.stdout.write(f"      Username: {username}")
        self.stdout.write(f"      Email: {email}")
        self.stdout.write(f"      Password: {password}")
        self.stdout.write(f"      Role: Admin")
        self.stdout.write("\n   ⚠️  IMPORTANT: Change this password immediately after login!")
