import csv
from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction

class Command(BaseCommand):
    help = 'Load CSV data into the specified model, handling complex structures like lists.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')
        parser.add_argument('model_name', type=str, help='The app_label.ModelName (e.g., "talent.PersonSkill")')

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
                with transaction.atomic():
                    self.process_row(model, row, User)

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded data from {csv_file} into {model_name}'))

    def process_row(self, model, row, User):
        # Convert boolean-like values and handle lists
        for field, value in row.items():
            if isinstance(value, str):
                if value.lower() == 'true':
                    row[field] = True
                elif value.lower() == 'false':
                    row[field] = False
                elif ',' in value:  # Potential list
                    row[field] = [item.strip() for item in value.split(',') if item.strip()]

        # Handle user_id for Person model
        if model._meta.model_name == 'Person':
            self.handle_person_model(model, row, User)
        elif model._meta.model_name == 'PersonSkill':
            self.handle_person_skill_model(model, row)
        else:
            self.handle_generic_model(model, row)

    def handle_person_model(self, model, row, User):
        user_id = row.pop('user_id', None)
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.create_or_update_person(model, row, user)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User with id {user_id} does not exist. Skipping this row."))
        else:
            self.stdout.write(self.style.WARNING("user_id is required for Person model. Skipping this row."))

    def handle_person_skill_model(self, model, row):
        expertise_ids = row.pop('expertise_ids', [])
        obj = self.create_or_update_object(model, row)
        
        if obj and expertise_ids:
            Expertise = apps.get_model('talent.Expertise')
            expertises = Expertise.objects.filter(id__in=expertise_ids)
            obj.expertise.set(expertises)

    def handle_generic_model(self, model, row):
        self.create_or_update_object(model, row)

    def create_or_update_person(self, model, data, user):
        try:
            obj, created = model.objects.update_or_create(
                user=user,
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {obj}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated: {obj}'))
            return obj
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating/updating Person: {str(e)}'))
            return None

    def create_or_update_object(self, model, data):
        try:
            obj, created = model.objects.update_or_create(**data)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {obj}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated: {obj}'))
            return obj
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating/updating {model._meta.model_name}: {str(e)}'))
            return None