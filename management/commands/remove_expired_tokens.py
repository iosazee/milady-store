from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

class Command(BaseCommand):
    help = 'Remove expired tokens from the token blacklist tables'

    def handle(self, *args, **options):
        # Remove expired tokens from token_blacklist_outstandingtoken
        outstanding_tokens = OutstandingToken.objects.filter(expires_at__lte=timezone.now())
        outstanding_count = outstanding_tokens.count()

        if outstanding_count > 0:
            outstanding_tokens.delete()
            self.stdout.write(self.style.SUCCESS(f'Removed {outstanding_count} expired tokens from the outstandingtoken table'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired tokens found in the outstandingtoken table'))

        # Remove expired tokens from token_blacklist_blacklistedtoken
        blacklisted_tokens = BlacklistedToken.objects.filter(expiration__lte=timezone.now())
        blacklisted_count = blacklisted_tokens.count()

        if blacklisted_count > 0:
            blacklisted_tokens.delete()
            self.stdout.write(self.style.SUCCESS(f'Removed {blacklisted_count} expired tokens from the blacklistedtoken table'))
        else:
            self.stdout.write(self.style.SUCCESS('No expired tokens found in the blacklistedtoken table'))


# command to trigger this script: python manage.py remove_expired_tokens
# python manage.py remove_expired_tokens
