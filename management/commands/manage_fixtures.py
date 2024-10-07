"""
Django management command for managing CSV fixtures.

This command provides functionality to export, import, validate, and convert fixtures.
It works with CSV files stored in each app's 'fixtures/csv' directory.

Usage:
    python manage.py manage_fixtures <action> [--app <app_name>]

Actions:
    export          - Export data from the database to CSV fixtures for all models in all apps
                      (or a specific app if --app is specified).
    import          - Import data from CSV fixtures into the database for all models in all apps
                      (or a specific app if --app is specified).
    validate        - Validate CSV fixtures against model definitions for all apps
                      (or a specific app if --app is specified).
    convert_json    - Convert existing JSON fixtures to CSV format for all apps
                      (or a specific app if --app is specified).

Options:
    --app <app_name>    Specify a single app to process instead of all apps.

Examples:
    1. Export fixtures for all apps:
       python manage.py manage_fixtures export

    2. Import fixtures for a specific app:
       python manage.py manage_fixtures import --app myapp

    3. Validate fixtures for all apps:
       python manage.py manage_fixtures validate

    4. Convert JSON fixtures to CSV for a specific app:
       python manage.py manage_fixtures convert_json --app myapp

Notes:
    - CSV files are stored in and read from each app's 'fixtures/csv' directory.
    - JSON files are read from each app's 'fixtures' directory when converting.
    - Always backup your database before performing import operations.
    - It's recommended to run import operations in a test environment first.

For more information, see the method docstrings within this file.
"""

import os
import csv
import json
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.core.serializers.json import DjangoJSONEncoder

class Command(BaseCommand):
    help = 'Manage CSV fixtures: export, import, validate, and convert from JSON'

    def add_arguments(self, parser):
        parser.add_argument('action', type=str, choices=['export', 'import', 'validate', 'convert_json'],
                            help='Action to perform on fixtures')
        parser.add_argument('--app', type=str, help='Specific app to process (optional)')


    def handle(self, *args, **options):
        action = options['action']
        specific_app = options.get('app')

        if specific_app:
            try:
                app_configs = [apps.get_app_config(specific_app)]
            except LookupError:
                raise CommandError(f"App '{specific_app}' not found")
        else:
            app_configs = apps.get_app_configs()

        for app_config in app_configs:
            if action == 'export':
                self.export_to_csv(app_config)
            elif action == 'import':
                self.import_from_csv(app_config)
            elif action == 'validate':
                self.validate_csv(app_config)
            elif action == 'convert_json':
                self.convert_json_to_csv(app_config)

        self.stdout.write(self.style.SUCCESS(f"{action.capitalize()} operation completed."))

    def export_to_csv(self, app_config):
        app_name = app_config.name
        csv_fixture_dir = os.path.join(app_name, 'fixtures', 'csv')
        os.makedirs(csv_fixture_dir, exist_ok=True)

        for model in app_config.get_models():
            model_name = model._meta.model_name
            csv_path = os.path.join(csv_fixture_dir, f"{model_name}.csv")

            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                fields = [field.name for field in model._meta.fields]
                writer.writerow(fields)

                for instance in model.objects.all():
                    row = [getattr(instance, field) for field in fields]
                    writer.writerow(row)

            self.stdout.write(self.style.SUCCESS(f"Exported {app_name}/{model_name} to CSV"))

    def import_from_csv(self, app_config):
        app_name = app_config.name
        csv_fixture_dir = os.path.join(app_name, 'fixtures', 'csv')

        if not os.path.exists(csv_fixture_dir):
            self.stdout.write(self.style.WARNING(f"No CSV fixtures found for app: {app_name}"))
            return

        for filename in os.listdir(csv_fixture_dir):
            if filename.endswith('.csv'):
                model_name = os.path.splitext(filename)[0]
                try:
                    model = app_config.get_model(model_name)
                except LookupError:
                    self.stdout.write(self.style.ERROR(f"No corresponding model found for CSV: {filename}"))
                    continue

                csv_path = os.path.join(csv_fixture_dir, filename)
                with open(csv_path, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        model.objects.create(**row)

                self.stdout.write(self.style.SUCCESS(f"Imported {app_name}/{model_name} from CSV"))

    def validate_csv(self, app_config):
        app_name = app_config.name
        csv_fixture_dir = os.path.join(app_name, 'fixtures', 'csv')

        if not os.path.exists(csv_fixture_dir):
            self.stdout.write(self.style.WARNING(f"No CSV fixtures found for app: {app_name}"))
            return

        for filename in os.listdir(csv_fixture_dir):
            if filename.endswith('.csv'):
                model_name = os.path.splitext(filename)[0]
                try:
                    model = app_config.get_model(model_name)
                except LookupError:
                    self.stdout.write(self.style.ERROR(f"No corresponding model found for CSV: {filename}"))
                    continue

                csv_path = os.path.join(csv_fixture_dir, filename)
                inconsistencies = self.validate_csv_against_model(csv_path, model)

                if inconsistencies:
                    self.stdout.write(self.style.ERROR(f"\nInconsistencies in {app_name}/{filename}:"))
                    for inconsistency in inconsistencies:
                        self.stdout.write(self.style.ERROR(f"- {inconsistency}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"\n{app_name}/{filename} is consistent with the model definition."))

    def validate_csv_against_model(self, csv_path, model):
        model_fields = {field.name: field for field in model._meta.fields}
        inconsistencies = []

        with open(csv_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            headers = reader.fieldnames

            csv_fields = set(headers)
            model_field_names = set(model_fields.keys())
            missing_fields = model_field_names - csv_fields
            extra_fields = csv_fields - model_field_names

            if missing_fields:
                inconsistencies.append(f"Missing fields in CSV: {', '.join(missing_fields)}")
            if extra_fields:
                inconsistencies.append(f"Extra fields in CSV: {', '.join(extra_fields)}")

            for row_num, row in enumerate(reader, start=2):
                for field_name, value in row.items():
                    if field_name not in model_fields:
                        continue
                    field = model_fields[field_name]
                    try:
                        field.clean(value, model())
                    except Exception as e:
                        inconsistencies.append(f"Row {row_num}, Field '{field_name}': {str(e)}")

        return inconsistencies

    def convert_json_to_csv(self, app_config):
        app_name = app_config.name
        json_fixture_dir = os.path.join(app_name, 'fixtures')
        csv_fixture_dir = os.path.join(app_name, 'fixtures', 'csv')
        os.makedirs(csv_fixture_dir, exist_ok=True)

        for filename in os.listdir(json_fixture_dir):
            if filename.endswith('.json'):
                json_path = os.path.join(json_fixture_dir, filename)
                csv_filename = os.path.splitext(filename)[0] + '.csv'
                csv_path = os.path.join(csv_fixture_dir, csv_filename)

                with open(json_path, 'r') as json_file:
                    data = json.load(json_file)

                if not data:
                    self.stdout.write(self.style.WARNING(f"No data found in {json_path}"))
                    continue

                fields = set()
                for item in data:
                    fields.update(item['fields'].keys())
                fields = sorted(fields)

                with open(csv_path, 'w', newline='') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=['id'] + fields)
                    writer.writeheader()

                    for item in data:
                        row = {'id': item['pk']}
                        row.update(item['fields'])
                        writer.writerow(row)

                self.stdout.write(self.style.SUCCESS(f"Converted {json_path} to {csv_path}"))