from decimal import Decimal
from django.core.management.base import BaseCommand
from django.apps import apps
import csv
from django.db import transaction, models, connection
from datetime import datetime, timezone
from django.utils import timezone as django_timezone
from django.core.exceptions import ObjectDoesNotExist
import traceback
import uuid
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware


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
            return [row for row in reader if any(row.values())]  # Skip empty rows

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
            'bountyclaim': BountyClaimParser(),
            'cartlineitem': CartLineItemParser(),
            'salesorderlineitem': SalesOrderLineItemParser(),
        }
        return parsers.get(model._meta.model_name.lower(), ModelParser())

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
            if isinstance(value, str):
                if value.lower() in ['true', 'false']:
                    parsed_row[key] = value.lower() == 'true'
                elif value.lower() in ['null', 'none', '']:
                    parsed_row[key] = None
                elif key in ['entry_deadline', 'judging_deadline']:
                    parsed_row[key] = parse_datetime(value)
                else:
                    parsed_row[key] = value
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
        
        # Convert empty strings to None for specific fields
        for field in ['claimed_by_id', 'competition_id', 'challenge_id', 'skill_id']:
            if parsed_row.get(field) == '':
                parsed_row[field] = None
        
        # Handle reward amount based on reward type
        if parsed_row.get('reward_type') == 'USD':
            parsed_row['reward_in_usd_cents'] = int(float(parsed_row.get('reward_amount', 0)) * 100)
            parsed_row['reward_in_points'] = None
        elif parsed_row.get('reward_type') == 'Points':
            parsed_row['reward_in_points'] = int(parsed_row.get('reward_amount', 0))
            parsed_row['reward_in_usd_cents'] = None
        
        # Remove fields that are not in the model
        parsed_row.pop('reward_amount', None)
        
        return parsed_row

    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        # Fetch related objects
        Challenge = apps.get_model('product_management.Challenge')
        Competition = apps.get_model('product_management.Competition')
        Skill = apps.get_model('talent.Skill')
        
        try:
            challenge = Challenge.objects.get(id=parsed['challenge_id']) if parsed['challenge_id'] else None
        except Challenge.DoesNotExist:
            challenge = None
        
        try:
            competition = Competition.objects.get(id=parsed['competition_id']) if parsed['competition_id'] else None
        except Competition.DoesNotExist:
            competition = None
        
        try:
            skill = Skill.objects.get(id=parsed['skill_id']) if parsed['skill_id'] else None
        except Skill.DoesNotExist:
            skill = None

        defaults = {
            'title': parsed['title'],
            'description': parsed['description'],
            'status': parsed['status'],
            'reward_type': parsed['reward_type'],
            'reward_in_usd_cents': parsed.get('reward_in_usd_cents'),
            'reward_in_points': parsed.get('reward_in_points'),
            'challenge': challenge,
            'competition': competition,
            'skill': skill,
        }

        obj, created = model.objects.update_or_create(
            id=parsed['id'],
            defaults=defaults
        )

        return obj, created

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
            
            # Convert amounts to integer
            amount_in_usd_cents = int(parsed['amount_in_usd_cents']) if parsed['amount_in_usd_cents'] else None
            amount_in_points = int(parsed['amount_in_points']) if parsed['amount_in_points'] else None
            
            # Convert expected_finish_date to date object
            parsed['expected_finish_date'] = datetime.strptime(parsed['expected_finish_date'], "%Y-%m-%d").date()
            
            # Convert created_at and updated_at to timezone-aware datetime objects
            parsed['created_at'] = django_timezone.make_aware(datetime.strptime(parsed['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
            parsed['updated_at'] = django_timezone.make_aware(datetime.strptime(parsed['updated_at'], "%Y-%m-%dT%H:%M:%SZ"))
            
            # Try to get existing object or create a new one
            obj, created = model.objects.update_or_create(
                id=parsed['id'],
                defaults={
                    'bounty': bounty,
                    'person': person,
                    'amount_in_usd_cents': amount_in_usd_cents,
                    'amount_in_points': amount_in_points,
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
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        Cart = apps.get_model('commerce.Cart')

        cart = Cart.objects.get(id=parsed['cart_id'])
        
        sales_order, created = model.objects.update_or_create(
            id=parsed['id'],
            defaults={
                'cart': cart,
                'status': parsed['status'],
                'total_usd_cents_excluding_fees_and_taxes': int(parsed['total_usd_cents_excluding_fees_and_taxes']),
                'total_fees_usd_cents': int(parsed['total_fees_usd_cents']),
                'total_taxes_usd_cents': int(parsed['total_taxes_usd_cents']),
            }
        )

        return sales_order, created
    
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
        
class BountyClaimParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        # Fetch related objects
        Bounty = apps.get_model('product_management.Bounty')
        Person = apps.get_model('talent.Person')
        BountyBid = apps.get_model('talent.BountyBid')
        
        try:
            bounty = Bounty.objects.get(id=parsed['bounty_id'])
            person = Person.objects.get(id=parsed['person_id'])
            accepted_bid = BountyBid.objects.get(id=parsed['accepted_bid_id']) if parsed['accepted_bid_id'] else None
        except ObjectDoesNotExist as e:
            raise ValueError(f"Related object does not exist: {str(e)}")

        defaults = {
            'accepted_bid': accepted_bid,
            'status': parsed['status'],
            'created_at': django_timezone.make_aware(datetime.strptime(parsed['created_at'], "%Y-%m-%dT%H:%M:%SZ")),
            'updated_at': django_timezone.make_aware(datetime.strptime(parsed['updated_at'], "%Y-%m-%dT%H:%M:%SZ")),
        }

        obj, created = model.objects.update_or_create(
            id=parsed['id'],
            bounty=bounty,
            person=person,
            defaults=defaults
        )

        return obj, created
    
class CartLineItemParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        
        try:
            with transaction.atomic():
                # Parse the date strings correctly
                for date_field in ['created_at', 'updated_at']:
                    if parsed[date_field]:
                        parsed[date_field] = django_timezone.make_aware(
                            datetime.strptime(parsed[date_field], "%Y-%m-%d %H:%M:%S")
                        )

                # Handle adjustments
                if parsed['item_type'] in ['INCREASE_ADJUSTMENT', 'DECREASE_ADJUSTMENT']:
                    Bounty = apps.get_model('product_management.Bounty')
                    BountyBid = apps.get_model('talent.BountyBid')
                    
                    try:
                        bounty = Bounty.objects.get(id=parsed['bounty_id'])
                        bounty_bid = BountyBid.objects.get(id=parsed['related_bounty_bid_id'])
                        
                        # Check if a cart line item for this bounty already exists
                        existing_item = model.objects.filter(cart_id=parsed['cart_id'], bounty_id=parsed['bounty_id']).first()
                        
                        if existing_item:
                            # Update the existing item
                            existing_item.item_type = parsed['item_type']
                            existing_item.quantity = int(parsed['quantity'])
                            existing_item.unit_price_cents = int(parsed['unit_price_cents'])
                            existing_item.unit_price_points = int(parsed['unit_price_points'])
                            existing_item.updated_at = parsed['updated_at']
                            existing_item.metadata = existing_item.metadata or {}
                            existing_item.metadata['related_bounty_bid_id'] = parsed['related_bounty_bid_id']
                            existing_item.save()
                            return existing_item, False
                        else:
                            # Create a new item
                            cart_line_item = model.objects.create(
                                id=parsed['id'],
                                cart_id=parsed['cart_id'],
                                item_type=parsed['item_type'],
                                quantity=int(parsed['quantity']),
                                unit_price_cents=int(parsed['unit_price_cents']),
                                unit_price_points=int(parsed['unit_price_points']),
                                bounty_id=parsed['bounty_id'],
                                created_at=parsed['created_at'],
                                updated_at=parsed['updated_at'],
                                metadata={'related_bounty_bid_id': parsed['related_bounty_bid_id']}
                            )
                            return cart_line_item, True

                    except ObjectDoesNotExist:
                        print(f"Warning: Bounty or BountyBid not found for adjustment {parsed['id']}. Skipping.")
                        return None, False
                else:
                    # Handle non-adjustment items as before
                    cart_line_item, created = model.objects.update_or_create(
                        id=parsed['id'],
                        defaults={
                            'cart_id': parsed['cart_id'],
                            'item_type': parsed['item_type'],
                            'quantity': int(parsed['quantity']),
                            'unit_price_cents': int(parsed['unit_price_cents']),
                            'unit_price_points': int(parsed['unit_price_points']),
                            'bounty_id': parsed['bounty_id'] if parsed['bounty_id'] else None,
                            'created_at': parsed['created_at'],
                            'updated_at': parsed['updated_at']
                        }
                    )
                    return cart_line_item, created

        except Exception as e:
            print(f"Error processing row {parsed['id']}: {str(e)}")
            return None, False

class SalesOrderLineItemParser(ModelParser):
    def create_object(self, model, row):
        parsed = self.parse_row(row)
        SalesOrder = apps.get_model('commerce.SalesOrder')
        Bounty = apps.get_model('product_management.Bounty')

        try:
            sales_order = SalesOrder.objects.get(id=parsed['sales_order_id'])
        except ObjectDoesNotExist:
            print(f"Warning: SalesOrder with id {parsed['sales_order_id']} does not exist. Skipping this line item.")
            return None, False

        if parsed['item_type'] == 'BOUNTY':
            try:
                bounty = Bounty.objects.get(id=parsed['bounty_id'])
                if bounty.reward_type == 'USD':
                    reward_amount = bounty.reward_in_usd_cents
                elif bounty.reward_type == 'Points':
                    reward_amount = bounty.reward_in_points
                else:
                    print(f"Warning: Bounty with id {parsed['bounty_id']} has an invalid reward type. Skipping this line item.")
                    return None, False

                if reward_amount is None:
                    print(f"Warning: Bounty with id {parsed['bounty_id']} has no reward amount. Skipping this line item.")
                    return None, False

                if int(parsed['unit_price_cents']) != reward_amount:
                    print(f"Warning: Line item amount for Bounty {parsed['bounty_id']} is inconsistent with reward amount. Updating it.")
                    parsed['unit_price_cents'] = str(reward_amount)
            except ObjectDoesNotExist:
                print(f"Warning: Bounty with id {parsed['bounty_id']} does not exist. Skipping this line item.")
                return None, False
        else:
            bounty = None

        line_item, created = model.objects.update_or_create(
            id=parsed['id'],
            defaults={
                'sales_order': sales_order,
                'item_type': parsed['item_type'],
                'quantity': int(parsed['quantity']),
                'unit_price_cents': int(parsed['unit_price_cents']),
                'bounty': bounty,
                'fee_rate': Decimal(parsed['fee_rate']) if parsed['fee_rate'] else None,
                'tax_rate': Decimal(parsed['tax_rate']) if parsed['tax_rate'] else None,
            }
        )

        return line_item, created