import csv
import os
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime

class ModelParser:
    def parse_row(self, row):
        return {k: v for k, v in row.items() if v != ''}

    def create_object(self, model, row):
        obj, created = model.objects.update_or_create(
            id=int(row['id']),
            defaults=self.parse_row(row)
        )
        return obj, created

class UserParser(ModelParser):
    def parse_row(self, row):
        parsed = super().parse_row(row)
        boolean_fields = ['is_superuser', 'is_staff', 'is_active', 'password_reset_required', 'is_test_user']
        for field in boolean_fields:
            if field in parsed:
                parsed[field] = parsed[field].lower() == 'true'
        
        integer_fields = ['remaining_budget_for_failed_logins']
        for field in integer_fields:
            if field in parsed:
                parsed[field] = int(parsed[field])
        
        datetime_fields = ['last_login', 'date_joined']
        for field in datetime_fields:
            if field in parsed and parsed[field]:
                parsed[field] = parse_datetime(parsed[field])
        
        return parsed

class SkillParser(ModelParser):
    def parse_row(self, row):
        parsed = super().parse_row(row)
        parsed['active'] = parsed['active'].lower() == 'true'
        parsed['selectable'] = parsed['selectable'].lower() == 'true'
        parsed['display_boost_factor'] = int(parsed['display_boost_factor'])
        if 'parent_id' in parsed and parsed['parent_id']:
            parsed['parent_id'] = int(parsed['parent_id'])
        return parsed

    def post_process(self, model, objects):
        for obj in objects:
            if hasattr(obj, 'parent_id') and obj.parent_id:
                obj.parent = model.objects.get(id=obj.parent_id)
                obj.save()

class PersonParser(ModelParser):
    def parse_row(self, row):
        parsed = super().parse_row(row)
        User = get_user_model()
        if 'user_id' in parsed:
            parsed['user'] = User.objects.get(id=int(parsed['user_id']))
            del parsed['user_id']
        
        boolean_fields = ['send_me_bounties', 'completed_profile']
        for field in boolean_fields:
            if field in parsed:
                parsed[field] = parsed[field].lower() == 'true'
        
        integer_fields = ['points']
        for field in integer_fields:
            if field in parsed:
                parsed[field] = int(parsed[field])
        
        return parsed

class PersonSkillParser(ModelParser):
    def parse_row(self, row):
        parsed = super().parse_row(row)
        parsed['person_id'] = int(parsed['person_id'])
        parsed['skill_id'] = int(parsed['skill_id'])
        parsed['expertise_ids'] = [int(v) for v in parsed['expertise_ids'] if v]
        return parsed

    def create_object(self, model, row):
        parsed = self.parse_row(row)
        expertise_ids = parsed.pop('expertise_ids', [])
        obj, created = model.objects.update_or_create(
            id=int(parsed['id']),
            defaults={
                'person_id': parsed['person_id'],
                'skill_id': parsed['skill_id']
            }
        )
        if expertise_ids:
            Expertise = apps.get_model('talent.Expertise')
            obj.expertise.set(Expertise.objects.filter(id__in=expertise_ids))
        return obj, created

class ExpertiseParser(ModelParser):
    def parse_row(self, row):
        parsed = super().parse_row(row)
        if 'skill_id' in parsed:
            Skill = apps.get_model('talent.Skill')
            parsed['skill'] = Skill.objects.get(id=int(parsed['skill_id']))
            del parsed['skill_id']
        
        boolean_fields = ['selectable']
        for field in boolean_fields:
            if field in parsed:
                parsed[field] = parsed[field].lower() == 'true'
        
        integer_fields = ['parent_id']
        for field in integer_fields:
            if field in parsed and parsed[field]:
                parsed[field] = int(parsed[field])
            elif field in parsed and not parsed[field]:
                parsed[field] = None
        
        return parsed

class Command(BaseCommand):
    help = 'Load CSV data into the specified model.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        model_name = self.infer_model_name(csv_file)
        
        try:
            model = apps.get_model(model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f'Model "{model_name}" not found.'))
            return

        parser = self.get_parser(model)

        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            data = []
            for row in reader:
                row_dict = dict(zip(headers, row))
                if 'expertise_ids' in headers:
                    expertise_ids = [v for v in row[headers.index('expertise_ids'):] if v]
                    row_dict['expertise_ids'] = expertise_ids
                data.append(row_dict)

        with transaction.atomic():
            objects = self.create_objects(model, data, parser)
            if hasattr(parser, 'post_process'):
                parser.post_process(model, objects)

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded data from {csv_file} into {model_name}'))

    def infer_model_name(self, csv_file):
        parts = csv_file.split(os.sep)
        app_name = parts[-3]
        file_name = parts[-1].split('-')[0]
        if file_name == 'person':
            model_name = 'Person'
        elif file_name == 'person_skill':
            model_name = 'PersonSkill'
        else:
            model_name = file_name.capitalize()
        return f'{app_name}.{model_name}'

    def get_parser(self, model):
        parsers = {
            'user': UserParser(),
            'skill': SkillParser(),
            'person': PersonParser(),
            'personskill': PersonSkillParser(),
            'expertise': ExpertiseParser(),
        }
        return parsers.get(model._meta.model_name, ModelParser())

    def create_objects(self, model, data, parser):
        objects = []
        for row in data:
            try:
                obj, created = parser.create_object(model, row)
                objects.append(obj)
                status = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f'{status}: {obj}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating/updating object: {str(e)}. Row: {row}'))
        return objects