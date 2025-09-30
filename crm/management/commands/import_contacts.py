from django.core.management.base import BaseCommand
from crm.models import Contact
import csv
import json

class Command(BaseCommand):
    help = 'Import contacts from a CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            help='Skip contacts with existing phone numbers'
        )
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        skip_duplicates = options['skip_duplicates']
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                    try:
                        # Required fields
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        phone_number = row.get('phone_number', '').strip()
                        
                        if not all([first_name, last_name, phone_number]):
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Row {row_num}: Missing required fields (first_name, last_name, phone_number)'
                                )
                            )
                            error_count += 1
                            continue
                        
                        # Check for duplicates
                        if skip_duplicates and Contact.objects.filter(phone_number=phone_number).exists():
                            self.stdout.write(
                                self.style.WARNING(f'Row {row_num}: Contact with phone {phone_number} already exists')
                            )
                            skipped_count += 1
                            continue
                        
                        if dry_run:
                            self.stdout.write(
                                f'Would import: {first_name} {last_name} ({phone_number})'
                            )
                            imported_count += 1
                        else:
                            # Create contact
                            contact_data = {
                                'first_name': first_name,
                                'last_name': last_name,
                                'phone_number': phone_number,
                                'email': row.get('email', '').strip() or None,
                                'contact_type': row.get('contact_type', 'lead'),
                                'company': row.get('company', '').strip() or None,
                                'job_title': row.get('job_title', '').strip() or None,
                                'address_line1': row.get('address_line1', '').strip() or None,
                                'city': row.get('city', '').strip() or None,
                                'state': row.get('state', '').strip() or None,
                                'zip_code': row.get('zip_code', '').strip() or None,
                                'country': row.get('country', 'US'),
                                'lead_source': row.get('lead_source', '').strip() or None,
                                'best_time_to_call': row.get('best_time_to_call', '').strip() or None,
                                'timezone': row.get('timezone', 'UTC'),
                                'notes': row.get('notes', '').strip() or None,
                            }
                            
                            # Handle custom fields
                            custom_fields = {}
                            for key, value in row.items():
                                if key.startswith('custom_') and value.strip():
                                    custom_fields[key[7:]] = value.strip()  # Remove 'custom_' prefix
                            
                            if custom_fields:
                                contact_data['custom_fields'] = custom_fields
                            
                            contact = Contact.objects.create(**contact_data)
                            imported_count += 1
                            
                            self.stdout.write(f'Imported: {contact.full_name} ({contact.phone_number})')
                    
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'Row {row_num}: Error - {str(e)}')
                        )
                        error_count += 1
        
        except FileNotFoundError:
            raise CommandError(f'CSV file not found: {csv_file}')
        except Exception as e:
            raise CommandError(f'Error reading CSV file: {str(e)}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Import Summary ==='))
        if dry_run:
            self.stdout.write(f'Would import: {imported_count} contacts')
        else:
            self.stdout.write(f'Imported: {imported_count} contacts')
        self.stdout.write(f'Skipped: {skipped_count} contacts')
        self.stdout.write(f'Errors: {error_count} rows')
        
        if not dry_run and imported_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully imported {imported_count} contacts!')
            )
