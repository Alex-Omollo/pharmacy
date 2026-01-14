from django.core.management.base import BaseCommand
from core.models import User, Role

class Command(BaseCommand):
    help = 'Give a user admin role'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        try:
            admin_role = Role.objects.get(name='admin')
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin role not found'))
            return
        
        user.role = admin_role
        user.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ User "{username}" now has admin role'
        ))
        self.stdout.write(f'Is Admin: {user.is_admin}')
        self.stdout.write(f'Is Superuser: {user.is_superuser}')