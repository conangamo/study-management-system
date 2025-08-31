"""
Management command to cleanup old sessions
"""
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cleanup old sessions from database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Delete sessions older than this many days (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(days=days)
        
        # Find old sessions
        old_sessions = Session.objects.filter(expire_date__lt=cutoff_time)
        old_count = old_sessions.count()
        
        # Find invalid sessions
        invalid_sessions = Session.objects.filter(expire_date__isnull=True)
        invalid_count = invalid_sessions.count()
        
        total_count = old_count + invalid_count
        
        self.stdout.write(f"Found {old_count} old sessions (older than {days} days)")
        self.stdout.write(f"Found {invalid_count} invalid sessions (no expire_date)")
        self.stdout.write(f"Total sessions to delete: {total_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No sessions will be deleted"))
            return
        
        if total_count > 0:
            # Delete old sessions
            if old_count > 0:
                old_sessions.delete()
                self.stdout.write(f"Deleted {old_count} old sessions")
            
            # Delete invalid sessions
            if invalid_count > 0:
                invalid_sessions.delete()
                self.stdout.write(f"Deleted {invalid_count} invalid sessions")
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted {total_count} sessions")
            )
        else:
            self.stdout.write("No sessions to delete")
        
        # Show remaining sessions
        remaining = Session.objects.count()
        self.stdout.write(f"Remaining sessions: {remaining}") 