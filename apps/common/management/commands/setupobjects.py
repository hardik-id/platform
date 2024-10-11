from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Set up transactional objects programmatically'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to set up transactional objects...'))

        try:
            with transaction.atomic():
                self.create_carts()
                self.create_cart_line_items()
                self.create_platform_fee_cart_items()
                self.create_sales_tax_cart_items()
                self.create_sales_orders()
                self.create_sales_order_line_items()
                self.create_point_transactions()
                self.create_point_orders()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully set up all transactional objects'))

    def create_carts(self):
        Cart = apps.get_model('commerce.Cart')
        Person = apps.get_model('talent.Person')

        persons = Person.objects.all()[:5]  # Get the first 5 persons

        for person in persons:
            cart = Cart.objects.create(
                person=person,
                status='open'
            )
            self.stdout.write(self.style.SUCCESS(f'Created Cart: {cart}'))

    def create_cart_line_items(self):
        CartLineItem = apps.get_model('commerce.CartLineItem')
        Cart = apps.get_model('commerce.Cart')
        Bounty = apps.get_model('product_management.Bounty')

        carts = Cart.objects.all()
        bounties = Bounty.objects.all()[:10]  # Get the first 10 bounties

        for cart in carts:
            for bounty in bounties:
                cart_line_item = CartLineItem.objects.create(
                    cart=cart,
                    bounty=bounty,
                    amount_cents=bounty.reward_amount * 100  # Convert to cents
                )
                self.stdout.write(self.style.SUCCESS(f'Created CartLineItem: {cart_line_item}'))

    def create_platform_fee_cart_items(self):
        PlatformFeeCartItem = apps.get_model('commerce.PlatformFeeCartItem')
        Cart = apps.get_model('commerce.Cart')
        PlatformFeeConfiguration = apps.get_model('commerce.PlatformFeeConfiguration')

        carts = Cart.objects.all()
        fee_config = PlatformFeeConfiguration.objects.first()

        for cart in carts:
            platform_fee = PlatformFeeCartItem.objects.create(
                cart=cart,
                fee_configuration=fee_config,
                amount_cents=int(cart.total * fee_config.fee_rate)
            )
            self.stdout.write(self.style.SUCCESS(f'Created PlatformFeeCartItem: {platform_fee}'))

    def create_sales_tax_cart_items(self):
        SalesTaxCartItem = apps.get_model('commerce.SalesTaxCartItem')
        Cart = apps.get_model('commerce.Cart')

        carts = Cart.objects.all()
        tax_rate = Decimal('0.10')  # 10% tax rate

        for cart in carts:
            sales_tax = SalesTaxCartItem.objects.create(
                cart=cart,
                tax_rate=tax_rate,
                amount_cents=int(cart.total * tax_rate)
            )
            self.stdout.write(self.style.SUCCESS(f'Created SalesTaxCartItem: {sales_tax}'))

    def create_sales_orders(self):
        SalesOrder = apps.get_model('commerce.SalesOrder')
        Cart = apps.get_model('commerce.Cart')

        carts = Cart.objects.filter(status='open')

        for cart in carts:
            sales_order = SalesOrder.objects.create(
                cart=cart,
                status='pending',
                total_cents=int(cart.total * 100)
            )
            cart.status = 'closed'
            cart.save()
            self.stdout.write(self.style.SUCCESS(f'Created SalesOrder: {sales_order}'))

    def create_sales_order_line_items(self):
        SalesOrderLineItem = apps.get_model('commerce.SalesOrderLineItem')
        SalesOrder = apps.get_model('commerce.SalesOrder')
        CartLineItem = apps.get_model('commerce.CartLineItem')

        sales_orders = SalesOrder.objects.all()

        for sales_order in sales_orders:
            cart_line_items = CartLineItem.objects.filter(cart=sales_order.cart)
            for cart_line_item in cart_line_items:
                sales_order_line_item = SalesOrderLineItem.objects.create(
                    sales_order=sales_order,
                    bounty=cart_line_item.bounty,
                    amount_cents=cart_line_item.amount_cents
                )
                self.stdout.write(self.style.SUCCESS(f'Created SalesOrderLineItem: {sales_order_line_item}'))

    def create_point_transactions(self):
        PointTransaction = apps.get_model('commerce.PointTransaction')
        SalesOrder = apps.get_model('commerce.SalesOrder')
        ProductPointAccount = apps.get_model('commerce.ProductPointAccount')

        sales_orders = SalesOrder.objects.filter(status='completed')
        product_account = ProductPointAccount.objects.first()

        for sales_order in sales_orders:
            point_transaction = PointTransaction.objects.create(
                account=product_account,
                amount=sales_order.total_cents // 100,  # Convert cents to points
                transaction_type='credit',
                reference_object=sales_order
            )
            self.stdout.write(self.style.SUCCESS(f'Created PointTransaction: {point_transaction}'))

    def create_point_orders(self):
        PointOrder = apps.get_model('commerce.PointOrder')
        Person = apps.get_model('talent.Person')
        ProductPointAccount = apps.get_model('commerce.ProductPointAccount')

        persons = Person.objects.all()[:5]  # Get the first 5 persons
        product_account = ProductPointAccount.objects.first()

        for person in persons:
            point_order = PointOrder.objects.create(
                person=person,
                product_point_account=product_account,
                amount=1000,  # 1000 points
                status='completed'
            )
            self.stdout.write(self.style.SUCCESS(f'Created PointOrder: {point_order}'))
