import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from apps.product_management.models import Initiative, Product, Challenge, Bounty

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def product():
    return Product.objects.create(name='Test Product', slug='test-product')

@pytest.fixture
def initiative(product):
    return Initiative.objects.create(title='Test Initiative', product=product)

@pytest.fixture
def challenge(initiative):
    return Challenge.objects.create(title='Test Challenge', initiative=initiative, product=initiative.product, status=Challenge.ChallengeStatus.ACTIVE)

@pytest.fixture
def bounty(challenge):
    return Bounty.objects.create(
        title='Test Bounty',
        challenge=challenge,
        status=Bounty.BountyStatus.AVAILABLE,
        reward_type=Bounty.RewardType.POINTS,
        reward_amount=100
    )

@pytest.mark.django_db
class TestInitiativeListView:
    def test_initiative_list_view(self, client, initiative):
        url = reverse('initiative-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'initiatives' in response.context
        assert initiative in response.context['initiatives']

    def test_initiative_list_view_pagination(self, client, product):
        initiatives = [Initiative.objects.create(title=f'Initiative {i}', product=product) for i in range(15)]
        url = reverse('initiative-list')
        response = client.get(url)
        assert response.status_code == 200
        assert len(response.context['initiatives']) == 10
        
        response = client.get(f'{url}?page=2')
        assert response.status_code == 200
        assert len(response.context['initiatives']) == 5

@pytest.mark.django_db
class TestProductInitiativesView:
    def test_product_initiatives_view(self, client, product, initiative, bounty):
        url = reverse('product-initiatives', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 200
        assert 'initiatives' in response.context
        assert initiative in response.context['initiatives']
        assert response.context['initiatives'][0].total_points == 100

@pytest.mark.django_db
class TestInitiativeDetailView:
    def test_initiative_detail_view(self, client, product, initiative, challenge):
        url = reverse('initiative-detail', args=[product.slug, initiative.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['initiative'] == initiative
        assert 'challenges' in response.context
        assert challenge in response.context['challenges']
        assert 'bounty_status' in response.context

@pytest.mark.django_db
class TestCreateInitiativeView:
    def test_create_initiative_view(self, client, user, product):
        client.force_login(user)
        url = reverse('create-initiative', args=[product.slug])
        data = {
            'title': 'New Initiative',
            'description': 'Test description',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Initiative.objects.filter(title='New Initiative', product=product).exists()

    def test_create_initiative_view_unauthenticated(self, client, product):
        url = reverse('create-initiative', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

@pytest.mark.django_db
class TestUpdateInitiativeView:
    def test_update_initiative_view(self, client, user, product, initiative):
        client.force_login(user)
        url = reverse('update-initiative', args=[product.slug, initiative.pk])
        data = {
            'title': 'Updated Initiative',
            'description': 'Updated description',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        initiative.refresh_from_db()
        assert initiative.title == 'Updated Initiative'

    def test_update_initiative_view_unauthenticated(self, client, product, initiative):
        url = reverse('update-initiative', args=[product.slug, initiative.pk])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))