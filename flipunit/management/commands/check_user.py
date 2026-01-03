"""
Django management command to check user account status for admin login.

Usage:
    python manage.py check_user <username_or_email>
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Check user account status for admin login'

    def add_arguments(self, parser):
        parser.add_argument(
            'username_or_email',
            type=str,
            help='Username or email address to check',
        )

    def handle(self, *args, **options):
        username_or_email = options['username_or_email']
        
        # Try to find user by username or email
        try:
            if '@' in username_or_email:
                user = User.objects.get(email=username_or_email)
            else:
                user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ User "{username_or_email}" not found in database.'
                )
            )
            return
        except User.MultipleObjectsReturned:
            self.stdout.write(
                self.style.ERROR(
                    f'⚠️  Multiple users found with "{username_or_email}". This should not happen.'
                )
            )
            return
        
        # Check user status
        self.stdout.write(f'\n📋 User Account Information:')
        self.stdout.write(f'   Username: {user.username}')
        self.stdout.write(f'   Email: {user.email}')
        self.stdout.write(f'   Is Active: {user.is_active}')
        self.stdout.write(f'   Is Staff: {user.is_staff}')
        self.stdout.write(f'   Is Superuser: {user.is_superuser}')
        self.stdout.write(f'   Last Login: {user.last_login or "Never"}')
        self.stdout.write(f'   Date Joined: {user.date_joined}')
        
        # Check if user can login to admin
        issues = []
        if not user.is_active:
            issues.append('❌ User account is INACTIVE')
        if not user.is_staff:
            issues.append('❌ User is NOT a staff member (required for admin access)')
        if not user.is_superuser:
            issues.append('⚠️  User is NOT a superuser (but can still access admin if is_staff=True)')
        
        if issues:
            self.stdout.write(f'\n⚠️  Issues found:')
            for issue in issues:
                self.stdout.write(f'   {issue}')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ User account looks good for admin access!'
                )
            )
            self.stdout.write(
                '\n💡 If you still cannot login, try:'
            )
            self.stdout.write('   1. Clear browser cache and cookies')
            self.stdout.write('   2. Try incognito/private browsing mode')
            self.stdout.write('   3. Check for browser extensions blocking cookies')
            self.stdout.write('   4. Verify you are using the correct username (case-sensitive)')
            self.stdout.write('   5. Try a different browser')

