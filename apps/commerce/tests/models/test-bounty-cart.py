import pytest
from apps.commerce.models import BountyCart, BountyCartItem, PlatformFee

@pytest.mark.django_db
class TestBountyCart:
    @pytest.fixture
    def bounty_cart(self, user, product):
        return BountyCart.objects.create(user=user, product=product)

    def test_create_bounty_cart(self, bounty_cart):
        assert bounty_cart.status == BountyCart.BountyCartStatus.OPEN
        assert str(bounty_cart) == f"Bounty Cart for {bounty_cart.user.username} - {bounty_cart.product.name} (Open)"

    def test_calculate_platform_fee(self, bounty_cart, bounty, platform_fee_configuration):
        BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        bounty_cart.calculate_platform_fee()
        
        platform_fee = PlatformFee.objects.get(bounty_cart=bounty_cart)
        assert platform_fee.amount_cents == 1000
        assert platform_fee.fee_rate == 0.10

    def test_start_checkout(self, bounty_cart, bounty):
        BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        assert bounty_cart.start_checkout()
        assert bounty_cart.status == BountyCart.BountyCartStatus.CHECKOUT
        assert hasattr(bounty_cart, 'sales_order')

    def test_total_points(self, bounty_cart, bounty):
        bounty.reward_type = 'Points'
        bounty.save()
        BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=1000,
            funding_type='Points'
        )
        assert bounty_cart.total_points() == 1000

    def test_total_usd_cents(self, bounty_cart, bounty):
        BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        assert bounty_cart.total_usd_cents() == 10000

    def test_total_amount(self, bounty_cart, bounty, platform_fee_configuration):
        BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        bounty_cart.calculate_platform_fee()
        assert bounty_cart.total_amount == 110.00
