import pytest
from django.contrib.auth import get_user_model
from apps.commerce.models import Organisation, OrganisationPointAccount, BountyCart, BountyCartItem
from apps.product_management.models import Product, Bounty

User = get_user_model()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def organisation(db):
    return Organisation.objects.create(
        name="Test Organisation",
        country="NL",
        vat_number="NL123456789B01"
    )

@pytest.fixture
def organisation_point_account(db, organisation):
    return OrganisationPointAccount.objects.create(
        organisation=organisation,
        balance=1000
    )

@pytest.fixture
def product(db):
    return Product.objects.create(
        name="Test Product",
        description="A test product"
    )

@pytest.fixture
def bounty(db, product):
    return Bounty.objects.create(
        title="Test Bounty",
        description="A test bounty",
        product=product,
        reward_type=Bounty.RewardType.POINTS,
        reward_amount=100
    )

@pytest.fixture
def bounty_cart(db, user, product):
    return BountyCart.objects.create(
        user=user,
        product=product,
        status=BountyCart.BountyCartStatus.CREATED
    )

@pytest.fixture
def bounty_cart_item(db, bounty_cart, bounty):
    return BountyCartItem.objects.create(
        cart=bounty_cart,
        bounty=bounty,
        points=bounty.reward_amount
    )

@pytest.fixture
def bounty_cart_with_items(db, bounty_cart, bounty):
    BountyCartItem.objects.create(
        cart=bounty_cart,
        bounty=bounty,
        points=bounty.reward_amount
    )
    return bounty_cart