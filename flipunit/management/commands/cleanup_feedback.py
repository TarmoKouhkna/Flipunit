"""
Django management command to delete feedback older than 30 days.

Usage:
    python manage.py cleanup_feedback [--days 30] [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from flipunit.models import Feedback


class Command(BaseCommand):
    help = 'Delete feedback entries older than specified days (default: 30 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep feedback (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find feedback older than cutoff date
        old_feedback = Feedback.objects.filter(created_at__lt=cutoff_date)
        count = old_feedback.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'✅ No feedback entries older than {days} days found.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'🔍 DRY RUN: Would delete {count} feedback entry/entries older than {days} days.'
                )
            )
            self.stdout.write(f'   Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            
            # Show sample entries
            sample = old_feedback[:5]
            if sample:
                self.stdout.write('\n   Sample entries that would be deleted:')
                for feedback in sample:
                    preview = feedback.message[:50] + '...' if len(feedback.message) > 50 else feedback.message
                    self.stdout.write(
                        f'   - {feedback.created_at.strftime("%Y-%m-%d")}: {preview}'
                    )
                if count > 5:
                    self.stdout.write(f'   ... and {count - 5} more')
        else:
            # Actually delete the feedback
            deleted_count = old_feedback.delete()[0]
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Successfully deleted {deleted_count} feedback entry/entries older than {days} days.'
                )
            )
            self.stdout.write(f'   Cutoff date: {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}')
            
            # Show remaining count
            remaining = Feedback.objects.count()
            self.stdout.write(f'   Remaining feedback entries: {remaining}')





























