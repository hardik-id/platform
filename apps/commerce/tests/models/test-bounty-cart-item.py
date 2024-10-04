import pytest
from django.core.exceptions import ValidationError
from apps.commerce.models import BountyCartItem

@pytest.mark.django_db
class TestBountyCartItem:
    @pytest.fixture
    def bounty_cart(self, user, product):
        from apps.commerce.models import BountyCart
        return BountyCart.objects.create(user=user, product=product)

    def test_create_bounty_cart_item(self, bounty_cart, bounty):
        item = BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=100,
            funding_type='USD'
        )
        assert str(item) == f"Funding for {bounty.title} in {bounty_cart}"

    def test_invalid_funding_type(self, bounty_cart, bounty):
        with pytest.raises(ValidationError):
            BountyCartItem.objects.create(
                cart=bounty_cart,
                bounty=bounty,
                funding_amount=100,
                funding_type='Points'
            )

    def test_invalid_funding_amount(self, bounty_cart, bounty):
        with pytest.raises(ValidationError):
            BountyCartItem.objects.create(
                cart=bounty_cart,
                bounty=bounty,
                funding_amount=200,
                funding_type='USD'
            )

    def test_points_property(self, bounty_cart, bounty):
        bounty.reward_type = 'Points'
        bounty.reward_amount = 100
        bounty.save()
        item = BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=100,
            funding_type='Points'
        )
        assert item.points == 100
        assert item.usd_amount == 0

    def test_usd_amount_property(self, bounty_cart, bounty):
        item = BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            funding_amount=10000,
            funding_type='USD'
        )
        assert item.points == 0
        assert item.usd_amount == 100.00
