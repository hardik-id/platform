import pytest
from django.core.exceptions import ValidationError
from apps.commerce.models import SalesOrder, BountyCart, BountyCartItem, PlatformFee

@pytest.mark.django_db
class TestSalesOrder:
    @pytest.fixture
    def bounty_cart(self, user, product, bounty):
        cart = BountyCart.objects.create(user=user, product=product)
        BountyCartItem.objects.create(
            cart=cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        cart.calculate_platform_fee()
        return cart

    def test_create_sales_order(self, bounty_cart):
        sales_order = SalesOrder.objects.create(
            bounty_cart=bounty_cart,
            total_usd_cents=11000
        )
        assert sales_order.status == SalesOrder.OrderStatus.PENDING
        assert str(sales_order) == f"Order {sales_order.id} for Cart {bounty_cart.id}"

    def test_calculate_total_usd_cents(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart)
        assert sales_order.calculate_total_usd_cents() == 11000

    def test_calculate_tax(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart, tax_rate=0.1)
        sales_order.calculate_tax()
        assert sales_order.tax_amount_cents == 1100

    def test_total_usd_property(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart, total_usd_cents=11000)
        assert sales_order.total_usd == 110.00

    def test_subtotal_property(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart, total_usd_cents=11000, tax_amount_cents=1000)
        assert sales_order.subtotal_cents == 10000
        assert sales_order.subtotal == 100.00

    @pytest.mark.django_db(transaction=True)
    def test_process_payment(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart)
        assert sales_order.process_payment()
        assert sales_order.status == SalesOrder.OrderStatus.COMPLETED
        assert bounty_cart.status == BountyCart.BountyCartStatus.COMPLETED

    @pytest.mark.django_db(transaction=True)
    def test_refund(self, bounty_cart):
        sales_order = SalesOrder.objects.create(bounty_cart=bounty_cart)
        sales_order.process_payment()
        assert sales_order.refund()
        assert sales_order.status == SalesOrder.OrderStatus.REFUNDED
