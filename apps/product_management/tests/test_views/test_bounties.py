import pytest
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import User
from apps.product_management.models import Bounty, Challenge, Product
from apps.product_management.views.bounties import (
    BountyListView, ProductBountyListView, BountyDetailView,
    CreateBountyView, UpdateBountyView, DeleteBountyView,
    BountyClaimView, DeleteBountyClaimView, DashboardProductBountiesView,
    DashboardProductBountyFilterView
)
from apps.talent.models import Skill, Expertise, BountyClaim

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def product():
    return Product.objects.create(name='Test Product', slug='test-product')

@pytest.fixture
def challenge(product):
    return Challenge.objects.create(title='Test Challenge', product=product)

@pytest.fixture
def bounty(challenge):
    return Bounty.objects.create(title='Test Bounty', challenge=challenge, status=Bounty.BountyStatus.AVAILABLE)

@pytest.fixture
def bounty_claim(bounty, user):
    return BountyClaim.objects.create(bounty=bounty, person=user.person, status=BountyClaim.Status.REQUESTED)

@pytest.mark.django_db
class TestBountyListView:
    def test_bounty_list_view(self, client, bounty):
        url = reverse('bounty-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounties' in response.context
        assert bounty in response.context['bounties']

    def test_bounty_list_view_htmx(self, client, bounty):
        url = reverse('bounty-list')
        response = client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200
        assert 'product_management/bounty/partials/list_partials.html' in [t.name for t in response.templates]

    def test_bounty_list_view_filter(self, client, bounty):
        url = reverse('bounty-list') + f'?status={Bounty.BountyStatus.AVAILABLE}'
        response = client.get(url)
        assert response.status_code == 200
        assert bounty in response.context['bounties']

@pytest.mark.django_db
class TestProductBountyListView:
    def test_product_bounty_list_view(self, client, product, bounty):
        url = reverse('product-bounties', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounties' in response.context
        assert bounty in response.context['bounties']

@pytest.mark.django_db
class TestBountyDetailView:
    def test_bounty_detail_view(self, client, bounty):
        url = reverse('bounty-detail', args=[bounty.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['bounty'] == bounty

@pytest.mark.django_db
class TestCreateBountyView:
    def test_create_bounty_view(self, client, user, challenge):
        client.force_login(user)
        url = reverse('create-bounty', args=[challenge.product.slug, challenge.pk])
        skill = Skill.objects.create(name='Test Skill')
        data = {
            'title': 'New Bounty',
            'description': 'Test description',
            'skill': skill.id,
            'expertise_ids': '',
            'status': Bounty.BountyStatus.AVAILABLE,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Bounty.objects.filter(title='New Bounty').exists()

@pytest.mark.django_db
class TestUpdateBountyView:
    def test_update_bounty_view(self, client, user, bounty):
        client.force_login(user)
        url = reverse('update-bounty', args=[bounty.challenge.product.slug, bounty.pk])
        data = {
            'title': 'Updated Bounty',
            'description': bounty.description,
            'skill': bounty.skill.id,
            'expertise_ids': '',
            'status': bounty.status,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        bounty.refresh_from_db()
        assert bounty.title == 'Updated Bounty'

@pytest.mark.django_db
class TestDeleteBountyView:
    def test_delete_bounty_view(self, client, user, bounty):
        client.force_login(user)
        url = reverse('delete-bounty', args=[bounty.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert not Bounty.objects.filter(pk=bounty.pk).exists()

@pytest.mark.django_db
class TestBountyClaimView:
    def test_bounty_claim_view(self, client, user, bounty):
        client.force_login(user)
        url = reverse('bounty-claim', args=[bounty.pk])
        data = {'notes': 'Test claim'}
        response = client.post(url, data)
        assert response.status_code == 200
        assert BountyClaim.objects.filter(bounty=bounty, person=user.person).exists()

@pytest.mark.django_db
class TestDeleteBountyClaimView:
    def test_delete_bounty_claim_view(self, client, user, bounty_claim):
        client.force_login(user)
        url = reverse('delete-bounty-claim', args=[bounty_claim.pk])
        response = client.post(url)
        assert response.status_code == 302
        bounty_claim.refresh_from_db()
        assert bounty_claim.status == BountyClaim.Status.CANCELLED

@pytest.mark.django_db
class TestDashboardProductBountiesView:
    def test_dashboard_product_bounties_view(self, client, user, product, bounty_claim):
        client.force_login(user)
        url = reverse('dashboard-product-bounties', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounty_claims' in response.context
        assert bounty_claim in response.context['bounty_claims']

@pytest.mark.django_db
class TestDashboardProductBountyFilterView:
    def test_dashboard_product_bounty_filter_view(self, client, user, product, bounty):
        client.force_login(user)
        url = reverse('dashboard-product-bounty-filter', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounties' in response.context
        assert bounty in response.context['bounties']

    def test_dashboard_product_bounty_filter_view_with_search(self, client, user, product, bounty):
        client.force_login(user)
        url = reverse('dashboard-product-bounty-filter', args=[product.slug]) + f'?search-bounty={bounty.challenge.title}'
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounties' in response.context
        assert bounty in response.context['bounties']

    def test_dashboard_product_bounty_filter_view_with_sort(self, client, user, product, bounty):
        client.force_login(user)
        url = reverse('dashboard-product-bounty-filter', args=[product.slug]) + '?q=sort:reward-desc'
        response = client.get(url)
        assert response.status_code == 200
        assert 'bounties' in response.context
        assert bounty in response.context['bounties']