from django.core.management.base import BaseCommand, CommandError
from calls.tasks import bulk_process_call_queue
from calls.models import CallQueue
from django.utils import timezone

class Command(BaseCommand):
    help = 'Process pending calls in the call queue'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of calls to process (default: 10)'
        )
        parser.add_argument(
            '--priority',
            type=str,
            choices=['low', 'normal', 'high', 'urgent'],
            help='Process only calls with specific priority'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        priority = options['priority']
        dry_run = options['dry_run']
        
        # Build query
        queryset = CallQueue.objects.filter(
            status='pending',
            scheduled_time__lte=timezone.now()
        )
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        queryset = queryset.order_by('priority', 'scheduled_time')[:limit]
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Would process {queryset.count()} calls:')
            )
            for item in queryset:
                self.stdout.write(
                    f'  - {item.contact.full_name} ({item.contact.phone_number}) '
                    f'- Priority: {item.priority} - Scheduled: {item.scheduled_time}'
                )
        else:
            if queryset.count() == 0:
                self.stdout.write(
                    self.style.WARNING('No pending calls to process')
                )
                return
            
            self.stdout.write(
                self.style.SUCCESS(f'Processing {queryset.count()} calls...')
            )
            
            result = bulk_process_call_queue()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully queued {result["processed_items"]} calls for processing'
                )
            )
            
            for item in result['results']:
                self.stdout.write(
                    f'  - Queue item {item["queue_item_id"]} -> Task {item["task_id"]}'
                )
