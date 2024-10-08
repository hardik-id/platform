import csv
from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Load CSV data into the specified model.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')
        parser.add_argument('model_name', type=str, help='The app_label.ModelName (e.g., "talent.Person")')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        model_name = kwargs['model_name']

        try:
            model = apps.get_model(model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f'Model "{model_name}" not found.'))
            return

        User = get_user_model()

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Convert boolean-like values
                for field, value in row.items():
                    if value.lower() == 'true':
                        row[field] = True
                    elif value.lower() == 'false':
                        row[field] = False

                # Handle user_id for Person model
                if model_name == 'talent.Person':
                    user_id = row.pop('user_id', None)
                    if user_id:
                        try:
                            user = User.objects.get(id=user_id)
                            row['user'] = user
                        except User.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"User with id {user_id} does not exist. Skipping this row."))
                            continue
                    else:
                        self.stdout.write(self.style.WARNING("user_id is required for Person model. Skipping this row."))
                        continue

                # Create a dictionary for model instantiation
                data = {field: value for field, value in row.items() if field in [f.name for f in model._meta.fields]}

                try:
                    obj, created = model.objects.get_or_create(**data)

                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Created: {obj}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Already exists: {obj}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating/updating {model_name}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded data from {csv_file} into {model_name}'))