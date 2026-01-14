from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Initialize default roles for POS system'

    def handle(self, *args, **kwargs):
        roles = [
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
        
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created role: {role.get_name_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Role already exists: {role.get_name_display()}')
                )