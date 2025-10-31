from django.core.management.base import BaseCommand
from shared.projects.models import SustainableDevelopmentGoal


class Command(BaseCommand):
    help = 'Populate the database with all 17 Sustainable Development Goals'

    SDG_DATA = [
        {'goal_number': 1, 'name': 'No Poverty'},
        {'goal_number': 2, 'name': 'Zero Hunger'},
        {'goal_number': 3, 'name': 'Good Health and Well-being'},
        {'goal_number': 4, 'name': 'Quality Education'},
        {'goal_number': 5, 'name': 'Gender Equality'},
        {'goal_number': 6, 'name': 'Clean Water and Sanitation'},
        {'goal_number': 7, 'name': 'Affordable and Clean Energy'},
        {'goal_number': 8, 'name': 'Decent Work and Economic Growth'},
        {'goal_number': 9, 'name': 'Industry, Innovation and Infrastructure'},
        {'goal_number': 10, 'name': 'Reduced Inequality'},
        {'goal_number': 11, 'name': 'Sustainable Cities and Communities'},
        {'goal_number': 12, 'name': 'Responsible Consumption and Production'},
        {'goal_number': 13, 'name': 'Climate Action'},
        {'goal_number': 14, 'name': 'Life Below Water'},
        {'goal_number': 15, 'name': 'Life on Land'},
        {'goal_number': 16, 'name': 'Peace, Justice and Strong Institutions'},
        {'goal_number': 17, 'name': 'Partnerships for the Goals'},
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Checking existing SDGs...'))
        
        # Check existing SDGs
        existing_count = SustainableDevelopmentGoal.objects.count()
        existing_numbers = set(SustainableDevelopmentGoal.objects.values_list('goal_number', flat=True))
        
        if existing_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Found {existing_count} existing SDG(s): {sorted(existing_numbers)}')
            )
        
        # Track statistics
        created_count = 0
        skipped_count = 0
        updated_count = 0
        
        # Process each SDG
        for sdg_data in self.SDG_DATA:
            goal_number = sdg_data['goal_number']
            name = sdg_data['name']
            
            try:
                # Check if SDG already exists
                existing_sdg = SustainableDevelopmentGoal.objects.filter(goal_number=goal_number).first()
                
                if existing_sdg:
                    # Check if name needs updating
                    if existing_sdg.name != name:
                        existing_sdg.name = name
                        existing_sdg.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Updated SDG {goal_number}: {name}')
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⊘ Skipped SDG {goal_number}: {name} (already exists)')
                        )
                        skipped_count += 1
                else:
                    # Create new SDG
                    SustainableDevelopmentGoal.objects.create(**sdg_data)
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created SDG {goal_number}: {name}')
                    )
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing SDG {goal_number}: {str(e)}')
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Total SDGs in database: {SustainableDevelopmentGoal.objects.count()}')
        self.stdout.write('='*60)
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully populated SDG data!')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'\n⊙ All SDGs already exist - no changes made.')
            )
