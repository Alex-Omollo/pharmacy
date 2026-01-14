from django.core.management.base import BaseCommand
from core.models import User, Role

class Command(BaseCommand):
    help = 'Give admin role to all Django superusers'

    def handle(self, *args, **options):
        try:
            admin_role = Role.objects.get(name='admin')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin role not found'))
            return
        
        # Get all superusers without admin role
        superusers = User.objects.filter(is_superuser=True, role__isnull=True)
        
        count = 0
        for user in superusers:
            user.role = admin_role
            user.save()
            count += 1
            self.stdout.write(f'✅ {user.username} -> admin')
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No superusers found without admin role'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Updated {count} superusers'))