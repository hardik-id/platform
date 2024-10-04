import pytest
from apps.commerce.models import PlatformFee, BountyCart

@pytest.mark.django_db
class TestPlatformFee:
    @pytest.fixture
    def bounty_cart(self, user, product):
        return BountyCart.objects.create(user=user, product=product)

    def test_create_platform_fee(self, bounty_cart):
        platform_fee = PlatformFee.objects.create(
            bounty_cart=bounty_cart,
            amount_cents=1000,
            fee_rate=0.10
        )
        assert platform_fee.amount == 10.00
        assert str(platform_fee) == f"Platform Fee: $10.00 for Cart {bounty_cart.id}"
