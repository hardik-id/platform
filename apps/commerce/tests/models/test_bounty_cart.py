import pytest
from apps.commerce.models import BountyCart, BountyCartItem

@pytest.mark.django_db
class TestBountyCart:
    def test_create_bounty_cart(self, user, product):
        cart = BountyCart.objects.create(
            user=user,
            product=product,
            status=BountyCart.BountyCartStatus.CREATED
        )
        assert cart.user == user
        assert cart.product == product
        assert cart.status == BountyCart.BountyCartStatus.CREATED

    def test_total_points(self, bounty_cart_with_items):
        assert bounty_cart_with_items.total_points() == 100

    def test_process_cart(self, bounty_cart_with_items, organisation_point_account):
        bounty_cart_with_items.organisation = organisation_point_account.organisation
        bounty_cart_with_items.save()
        assert bounty_cart_with_items.process_cart() == True
        bounty_cart_with_items.refresh_from_db()
        assert bounty_cart_with_items.status == BountyCart.BountyCartStatus.COMPLETED
        organisation_point_account.refresh_from_db()
        assert organisation_point_account.balance == 900  # 1000 initial - 100 for the bounty

@pytest.mark.django_db
class TestBountyCartItem:
    def test_create_bounty_cart_item(self, bounty_cart, bounty):
        item = BountyCartItem.objects.create(
            cart=bounty_cart,
            bounty=bounty,
            points=bounty.reward_amount
        )
        assert item.cart == bounty_cart
        assert item.bounty == bounty
        assert item.points == bounty.reward_amount