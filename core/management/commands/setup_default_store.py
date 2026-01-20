from django.core.management.base import BaseCommand
from core.models import Store, User, Role
from django.db import transaction


class Command(BaseCommand):
    help = 'Set up default store and assign admin users to it'

    def handle(self, *args, **options):
        self.stdout.write("Setting up default store...")
        
        with transaction.atomic():
            # Get or create default store
            default_store = Store.get_default_store()
            
            if default_store.created_by is None:
                # Find admin users
                admin_role = Role.objects.filter(name='admin').first()
                if admin_role:
                    admin_users = User.objects.filter(role=admin_role, is_active=True).first()
                    if admin_users:
                        default_store.created_by = admin_users
                        default_store.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"Default store '{default_store.name}' created and assigned to admin user")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING("No admin users found. Default store created without creator.")
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING("No admin role found. Default store created without creator.")
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Default store '{default_store.name}' already exists")
                )
            
            # Assign users without stores to the default store
            users_without_store = User.objects.filter(store__isnull=True, is_active=True)
            count = users_without_store.count()
            if count > 0:
                users_without_store.update(store=default_store)
                self.stdout.write(
                    self.style.SUCCESS(f"Assigned {count} users to default store")
                )
            
            self.stdout.write(
                self.style.SUCCESS("Default store setup completed!")
            )