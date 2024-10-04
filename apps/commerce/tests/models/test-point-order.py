import pytest
from apps.commerce.models import PointOrder, ProductPointAccount, BountyCart, BountyCartItem, PointTransaction

@pytest.mark.django_db
class TestPointOrder:
    @pytest.fixture
    def product_point_account(self, product):
        return ProductPointAccount.objects.create(product=product, balance=1000)

    @pytest.fixture
    def bounty_cart(self, user, product, bounty):
        cart = BountyCart.objects.create(user=user, product=product)
        bounty.reward_type = 'Points'
        bounty.reward_amount = 500
        bounty.save()
        BountyCartItem.objects.create(
            cart=cart,
            bounty=bounty,
            funding_amount=500,
            funding_type='Points'
        )
        return cart

    def test_create_point_order(self, product_point_account, bounty_cart, bounty):
        point_order = PointOrder.objects.create(
            product_account=product_point_account,
            bounty=bounty,
            bounty_cart=bounty_cart,
            amount=500
        )
        assert str(point_order) == f"Point Order of 500 points for {bounty.title} in Cart {bounty_cart.id}"

    @pytest.mark.django_db(transaction=True)
    def test_complete_point_order(self, product_point_account, bounty_cart, bounty):
        point_order = PointOrder.objects.create(
            product_account=product_point_account,
            bounty=bounty,
            bounty_cart=bounty_cart,
            amount=500
        )
        assert point_order.complete()
        assert point_order.status == 'COMPLETED'
        assert product_point_account.balance == 500
        
        transaction = PointTransaction.objects.first()
        assert transaction.product_account == product_point_account
        assert transaction.amount == 500
        assert transaction.transaction_type == 'USE'

    @pytest.mark.django_db(transaction=True)
    def test_refund_point_order(self, product_point_account, bounty_cart, bounty):
        point_order = PointOrder.objects.create(
            product_account=product_point_account,
            bounty=bounty,
            bounty_cart=bounty_cart,
            amount=500
        )
        point_order.complete()
        assert point_order.refund()
        assert point_order.status == 'REFUNDED'
        assert product_point_account.balance == 1000
        
        refund_transaction = PointTransaction.objects.last()
        assert refund_transaction.product_account == product_point_account
        assert refund_transaction.amount == 500
        assert refund_transaction.transaction_type == 'REFUND'

    def test_activate_deactivate_bounty(self, product_point_account, bounty_cart, bounty):
        point_order = PointOrder.objects.create(
            product_account=product_point_account,
            bounty=bounty,
            bounty_cart=bounty_cart,
            amount=500
        )
        point_order.complete()
        assert bounty.challenge.status == bounty.challenge.ChallengeStatus.ACTIVE

        point_order.refund()
        assert bounty.challenge.status == bounty.challenge.ChallengeStatus.DRAFT
