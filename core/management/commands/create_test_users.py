from django.core.management.base import BaseCommand
from core.models import User, Role


class Command(BaseCommand):
    help = 'Create test users for each role'

    def handle(self, *args, **kwargs):
        # Get roles
        admin_role = Role.objects.get(name='admin')
        manager_role = Role.objects.get(name='manager')
        cashier_role = Role.objects.get(name='cashier')

        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@pos.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': admin_role,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Admin user created: {admin.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user already exists: {admin.username}'))

        # Create manager user
        manager, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@pos.com',
                'first_name': 'Manager',
                'last_name': 'User',
                'role': manager_role,
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Manager user created: {manager.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Manager user already exists: {manager.username}'))

        # Create cashier user
        cashier, created = User.objects.get_or_create(
            username='cashier',
            defaults={
                'email': 'cashier@pos.com',
                'first_name': 'Cashier',
                'last_name': 'User',
                'role': cashier_role,
            }
        )
        if created:
            cashier.set_password('cashier123')
            cashier.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Cashier user created: {cashier.username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Cashier user already exists: {cashier.username}'))

        self.stdout.write(self.style.SUCCESS('\n=== Test Users Created ==='))
        self.stdout.write('Admin    - username: admin    password: admin123')
        self.stdout.write('Manager  - username: manager  password: manager123')
        self.stdout.write('Cashier  - username: cashier  password: cashier123')