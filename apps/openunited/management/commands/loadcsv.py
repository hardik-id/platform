
from django.core.management.base import BaseCommand
from django.apps import apps
import csv
from django.db import transaction, models

class Command(BaseCommand):
    help = 'Load data from a CSV file into the specified model.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The CSV file to load')
        parser.add_argument('--model', type=str, help='The model to use for the CSV file', required=True)

    def parse_csv(self, file_path):
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            return list(reader)

    def get_parser(self, model):
        parsers = {
            'personskill': PersonSkillParser(),
            'person': PersonParser(),
            'skill': SkillParser(),
            'expertise': ExpertiseParser(),
        }
        return parsers.get(model._meta.model_name, ModelParser())

    def create_objects(self, model, data, parser):
        created_objects = []
        for row in data:
            try:
                obj, created = parser.create_object(model, row)
                created_objects.append(obj)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating/updating object: {e}. Row: {row}"))
        return created_objects

    @transaction.atomic
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        model_name = options['model']

        try:
            # Load the specified model
            model = apps.get_model(model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f'Model {model_name} not found.'))
            return

        # Parse the CSV file
        data = self.parse_csv(csv_file)

        # Create objects
        parser = self.get_parser(model)
        objects = self.create_objects(model, data, parser)

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded data from {csv_file} into {model_name}'))

class ModelParser:
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        # Check if the 'id' field is a UUID or integer
        if isinstance(model._meta.get_field('id'), models.UUIDField):
            obj, created = model.objects.update_or_create(
                id=parsed['id'],  # Don't cast to int if it's a UUID
                defaults=parsed
            )
        else:
            obj, created = model.objects.update_or_create(
                id=int(parsed['id']),
                defaults=parsed
            )
        return obj, created

    def parse_row(self, row):
        # Parsing logic including boolean handling
        parsed_row = {}
        for key, value in row.items():
            if value.lower() in ['true', 'false']:
                parsed_row[key] = value.lower() == 'true'
            else:
                parsed_row[key] = value
        return parsed_row

class PersonParser(ModelParser):
    pass

class SkillParser(ModelParser):
    pass

class ExpertiseParser(ModelParser):
    pass

class PersonSkillParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)

        # Extract expertise IDs and remove them from parsed data
        expertise_ids = parsed.pop('expertise_ids', '')
        if isinstance(expertise_ids, str):
            expertise_ids = [int(x.strip()) for x in expertise_ids.split(',') if x]

        # Create or update the PersonSkill object
        obj, created = model.objects.update_or_create(
            id=int(parsed['id']),
            defaults={
                'person_id': parsed['person_id'],
                'skill_id': parsed['skill_id']
            }
        )

        # Set the expertise M2M relationship
        if expertise_ids:
            Expertise = apps.get_model('talent.Expertise')
            obj.expertise.set(Expertise.objects.filter(id__in=expertise_ids))

        return obj, created
