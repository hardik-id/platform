import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.product_management.models import Product, Challenge, Competition, Bounty

@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

@pytest.fixture
def organisation():
    from apps.commerce.models import Organisation
    return Organisation.objects.create(name='Test Org', country='US', tax_id='123456789')

@pytest.fixture
def product():
    return Product.objects.create(name='Test Product')

@pytest.fixture
def challenge(product):
    return Challenge.objects.create(
        product=product,
        title='Test Challenge',
        status=Challenge.ChallengeStatus.DRAFT
    )

@pytest.fixture
def competition(product):
    return Competition.objects.create(
        product=product,
        title='Test Competition',
        status=Competition.CompetitionStatus.DRAFT
    )

@pytest.fixture
def bounty(challenge):
    return Bounty.objects.create(
        challenge=challenge,
        title='Test Bounty',
        reward_amount=100,
        reward_type='USD'
    )

@pytest.fixture
def platform_fee_configuration():
    from apps.commerce.models import PlatformFeeConfiguration
    return PlatformFeeConfiguration.objects.create(
        percentage=10,
        applies_from_date=timezone.now()
    )
