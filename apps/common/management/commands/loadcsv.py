from decimal import Decimal
from django.core.management.base import BaseCommand
from django.apps import apps
import csv
from django.db import transaction, models, connection
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
from django.core.exceptions import ObjectDoesNotExist
import traceback


def debug_print(message):
    print(f"DEBUG: {message}")

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
            'bounty': BountyParser(),
            'bountybid': BountyBidParser(),
            'platformfee': PlatformFeeParser(),
            'salesorder': SalesOrderParser(),
            'organisation': OrganisationParser(),
            'productarea': ProductAreaParser(),
            'productpointaccount': ProductPointAccountParser(),
        }
        return parsers.get(model._meta.model_name, ModelParser())

    def create_objects(self, model, data, parser):
        updated_objects = []
        for row in data:
            try:
                obj, _ = parser.create_object(model, row)
                if obj is not None:
                    updated_objects.append(obj)
                    self.stdout.write(self.style.SUCCESS(f"Updated object: {obj}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating object: {str(e)}"))
                self.stdout.write(self.style.ERROR(f"Row data: {row}"))
                self.stdout.write(self.style.ERROR(f"Traceback: {traceback.format_exc()}"))
        return updated_objects

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        model_name = options['model']

        try:
            model = apps.get_model(model_name)
        except LookupError:
            self.stdout.write(self.style.ERROR(f'Model {model_name} not found.'))
            return

        data = self.parse_csv(csv_file)
        parser = self.get_parser(model)
        objects = self.create_objects(model, data, parser)

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {len(objects)} objects from {csv_file} into {model_name}'))

class ModelParser:
    def parse_row(self, row):
        parsed_row = {}
        for key, value in row.items():
            if value.lower() in ['true', 'false']:
                parsed_row[key] = value.lower() == 'true'
            elif 'deadline' in key.lower() and value:
                parsed_row[key] = django_timezone.make_aware(datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
            elif value == '':
                parsed_row[key] = None  # Convert empty strings to None for all fields
            else:
                parsed_row[key] = value
        return parsed_row

    def create_object(self, model, row):
        parsed = self.parse_row(row)
        obj, created = model.objects.update_or_create(
            id=parsed['id'],
            defaults=parsed
        )
        return obj, created

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
            expertise_ids = [x.strip() for x in expertise_ids.split(',') if x]

        # Create or update the PersonSkill object
        obj, created = model.objects.update_or_create(
            id=parsed['id'],
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

class BountyParser(ModelParser):
    def parse_row(self, row):
        parsed_row = super().parse_row(row)
        
        # Convert string 'null' to None for specific fields
        for field in ['claimed_by_id', 'competition_id']:
            if parsed_row.get(field) == 'null':
                parsed_row[field] = None
        
        # Ensure numeric fields are properly typed
        for field in ['reward_amount']:
            if parsed_row.get(field):
                parsed_row[field] = int(parsed_row[field])
        
        return parsed_row

class BountyBidParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        try:
            # Get the Bounty and Person models
            Bounty = apps.get_model('product_management.Bounty')
            Person = apps.get_model('talent.Person')
            
            # Check if the bounty and person exist
            try:
                bounty = Bounty.objects.get(id=parsed['bounty_id'])
                person = Person.objects.get(id=parsed['person_id'])
            except ObjectDoesNotExist as e:
                raise ValueError(f"Bounty with id {parsed['bounty_id']} or Person with id {parsed['person_id']} does not exist")
            
            # Convert amount to integer
            parsed['amount'] = int(parsed['amount'])
            
            # Convert expected_finish_date to date object
            parsed['expected_finish_date'] = datetime.strptime(parsed['expected_finish_date'], "%d/%m/%Y").date()
            
            # Convert created_at and updated_at to timezone-aware datetime objects
            parsed['created_at'] = timezone.make_aware(datetime.strptime(parsed['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
            parsed['updated_at'] = timezone.make_aware(datetime.strptime(parsed['updated_at'], "%Y-%m-%dT%H:%M:%SZ"))
            
            # Try to get existing object or create a new one
            obj, created = model.objects.update_or_create(
                id=parsed['id'],
                defaults={
                    'bounty': bounty,
                    'person': person,
                    'amount': parsed['amount'],
                    'expected_finish_date': parsed['expected_finish_date'],
                    'status': parsed['status'],
                    'message': parsed['message'],
                    'created_at': parsed['created_at'],
                    'updated_at': parsed['updated_at'],
                }
            )
            
            return obj, created
        
        except Exception as e:
            raise ValueError(f"Error processing row: {str(e)}")
        
class PlatformFeeParser(ModelParser):
    def parse_row(self, row):
        parsed_row = super().parse_row(row)
        
        # Convert amount_cents to integer
        if 'amount_cents' in parsed_row:
            parsed_row['amount_cents'] = int(parsed_row['amount_cents'])
        
        # Convert fee_rate to Decimal
        if 'fee_rate' in parsed_row:
            parsed_row['fee_rate'] = Decimal(parsed_row['fee_rate'])
        
        return parsed_row
    
class SalesOrderParser(ModelParser):
    def parse_row(self, row):
        parsed_row = super().parse_row(row)
        
        # Convert numeric fields to appropriate types
        if 'total_usd_cents' in parsed_row:
            parsed_row['total_usd_cents'] = int(parsed_row['total_usd_cents'])
        
        if 'tax_rate' in parsed_row:
            parsed_row['tax_rate'] = Decimal(parsed_row['tax_rate'])
        
        if 'tax_amount_cents' in parsed_row:
            parsed_row['tax_amount_cents'] = int(parsed_row['tax_amount_cents'])
        
        return parsed_row

    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        BountyCart = apps.get_model('commerce.BountyCart')
        PlatformFee = apps.get_model('commerce.PlatformFee')
        
        bounty_cart = BountyCart.objects.get(id=parsed['bounty_cart_id'])
        platform_fee = PlatformFee.objects.get(id=parsed['platform_fee_id'])
        
        obj, created = model.objects.update_or_create(
            id=parsed['id'],
            defaults={
                'bounty_cart': bounty_cart,
                'status': parsed['status'],
                'total_usd_cents': parsed['total_usd_cents'],
                'platform_fee': platform_fee,
                'tax_rate': parsed['tax_rate'],
                'tax_amount_cents': parsed['tax_amount_cents']
            }
        )
        return obj, created

class OrganisationParser(ModelParser):
    def parse_row(self, row):
        parsed_row = super().parse_row(row)
        
        # Convert datetime strings to timezone-aware datetime objects
        for field in ['created_at', 'updated_at']:
            if parsed_row.get(field):
                # Parse the datetime string and keep its timezone information
                dt = datetime.strptime(parsed_row[field], "%Y-%m-%d %H:%M:%S%z")
                # Convert to UTC
                parsed_row[field] = dt.astimezone(timezone.utc)
        
        return parsed_row
    
class ProductAreaParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        path = parsed.pop('path')
        depth = int(parsed.pop('depth'))
        numchild = int(parsed.pop('numchild'))
        
        with transaction.atomic():
            # Check if the object already exists
            try:
                obj = model.objects.get(id=parsed['id'])
                for key, value in parsed.items():
                    setattr(obj, key, value)
                created = False
            except model.DoesNotExist:
                obj = model(**parsed)
                created = True

            # Set tree-specific fields
            obj.depth = depth
            obj.path = path
            obj.numchild = numchild

            # Save the object
            obj.save()

            # If it's a new object and not a root node, set its parent
            if created and depth > 1:
                parent_path = path[:-4]
                try:
                    parent = model.objects.get(path=parent_path)
                    obj.move(parent, pos='last-child')
                except model.DoesNotExist:
                    print(f"Warning: Parent with path {parent_path} does not exist for {obj}.")

        return obj, created
    
class ProductPointAccountParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        Product = apps.get_model('product_management.Product')
        
        try:
            product = Product.objects.get(id=parsed['product_id'])
            point_account = product.product_point_account
            point_account.balance = int(parsed['balance'])
            point_account.save()
            print(f"Updated ProductPointAccount for product {product.id}: balance = {point_account.balance}")
            return point_account, False
        except Product.DoesNotExist:
            print(f"WARNING: Product with id {parsed['product_id']} does not exist. Skipping this ProductPointAccount.")
            return None, False
        except model.DoesNotExist:
            print(f"WARNING: ProductPointAccount for product {parsed['product_id']} does not exist. This shouldn't happen due to the OneToOne relationship.")
            return None, False