from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import School, UserProfile


class Command(BaseCommand):
    help = 'Create or reset an admin staff user for login.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
        parser.add_argument('--password', default='admin123', help='Admin password (default: admin123)')
        parser.add_argument('--email', default='admin@school.local', help='Admin email')
        parser.add_argument('--school', default='Default School', help='School name for the admin user')
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Reset password if the user already exists',
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']
        school_name = options['school']
        reset_password = options['reset_password']
        school, _ = School.objects.get_or_create(name=school_name, defaults={'address': ''})

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={'school': school})
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {username}'))
            self.stdout.write(self.style.WARNING(f'Password: {password}'))
            return

        if reset_password:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.save()
            UserProfile.objects.update_or_create(user=user, defaults={'school': school})
            self.stdout.write(self.style.SUCCESS(f'Updated password for admin user: {username}'))
            self.stdout.write(self.style.WARNING(f'New password: {password}'))
            return

        self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
        self.stdout.write('Use --reset-password to update credentials.')
