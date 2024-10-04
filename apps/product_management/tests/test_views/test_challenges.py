import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from apps.product_management.models import Challenge, Product, Bounty
from apps.product_management.views.challenges import (
    ChallengeListView, ProductChallengesView, ChallengeDetailView,
    CreateChallengeView, UpdateChallengeView, DeleteChallengeView
)

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def product():
    return Product.objects.create(name='Test Product', slug='test-product')

@pytest.fixture
def challenge(product, user):
    return Challenge.objects.create(
        title='Test Challenge',
        description='Test Description',
        product=product,
        status=Challenge.ChallengeStatus.ACTIVE,
        created_by=user.person
    )

@pytest.mark.django_db
class TestChallengeListView:
    def test_challenge_list_view(self, client, challenge):
        url = reverse('challenge-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'challenges' in response.context
        assert challenge in response.context['challenges']

    def test_challenge_list_view_exclude_draft(self, client, product):
        draft_challenge = Challenge.objects.create(
            title='Draft Challenge',
            product=product,
            status=Challenge.ChallengeStatus.DRAFT
        )
        url = reverse('challenge-list')
        response = client.get(url)
        assert response.status_code == 200
        assert draft_challenge not in response.context['challenges']

@pytest.mark.django_db
class TestProductChallengesView:
    def test_product_challenges_view(self, client, challenge):
        url = reverse('product-challenges', args=[challenge.product.slug])
        response = client.get(url)
        assert response.status_code == 200
        assert 'challenges' in response.context
        assert challenge in response.context['challenges']

    def test_product_challenges_view_ordering(self, client, product):
        Challenge.objects.create(title='Active', product=product, status=Challenge.ChallengeStatus.ACTIVE)
        Challenge.objects.create(title='Blocked', product=product, status=Challenge.ChallengeStatus.BLOCKED)
        Challenge.objects.create(title='Completed', product=product, status=Challenge.ChallengeStatus.COMPLETED)
        
        url = reverse('product-challenges', args=[product.slug])
        response = client.get(url)
        challenges = list(response.context['challenges'])
        assert challenges[0].status == Challenge.ChallengeStatus.ACTIVE
        assert challenges[1].status == Challenge.ChallengeStatus.BLOCKED
        assert challenges[2].status == Challenge.ChallengeStatus.COMPLETED

@pytest.mark.django_db
class TestChallengeDetailView:
    def test_challenge_detail_view(self, client, challenge, user):
        url = reverse('challenge-detail', args=[challenge.product.slug, challenge.pk])
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['challenge'] == challenge
        
        client.force_login(user)
        response = client.get(url)
        assert 'agreement_status' in response.context
        assert 'agreement_template' in response.context

    def test_challenge_detail_view_with_bounties(self, client, challenge):
        Bounty.objects.create(title='Test Bounty', challenge=challenge, status=Bounty.BountyStatus.AVAILABLE)
        url = reverse('challenge-detail', args=[challenge.product.slug, challenge.pk])
        response = client.get(url)
        assert 'bounties' in response.context
        assert len(response.context['bounties']) == 1

@pytest.mark.django_db
class TestCreateChallengeView:
    def test_create_challenge_view(self, client, user, product):
        client.force_login(user)
        url = reverse('create-challenge', args=[product.slug])
        data = {
            'title': 'New Challenge',
            'description': 'Test description',
            'status': Challenge.ChallengeStatus.ACTIVE,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Challenge.objects.filter(title='New Challenge').exists()

    def test_create_challenge_view_unauthenticated(self, client, product):
        url = reverse('create-challenge', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

@pytest.mark.django_db
class TestUpdateChallengeView:
    def test_update_challenge_view(self, client, user, challenge):
        client.force_login(user)
        url = reverse('update-challenge', args=[challenge.product.slug, challenge.pk])
        data = {
            'title': 'Updated Challenge',
            'description': challenge.description,
            'status': challenge.status,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        challenge.refresh_from_db()
        assert challenge.title == 'Updated Challenge'

    def test_update_challenge_view_unauthenticated(self, client, challenge):
        url = reverse('update-challenge', args=[challenge.product.slug, challenge.pk])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

@pytest.mark.django_db
class TestDeleteChallengeView:
    def test_delete_challenge_view(self, client, user, challenge):
        client.force_login(user)
        url = reverse('delete-challenge', args=[challenge.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert not Challenge.objects.filter(pk=challenge.pk).exists()
        messages = list(get_messages(response.wsgi_request))
        assert any(message.message == "The challenge has been successfully deleted!" for message in messages)

    def test_delete_challenge_view_unauthorized(self, client, challenge):
        unauthorized_user = User.objects.create_user(username='unauthorized', password='12345')
        client.force_login(unauthorized_user)
        url = reverse('delete-challenge', args=[challenge.pk])
        response = client.post(url)
        assert response.status_code == 302
        assert Challenge.objects.filter(pk=challenge.pk).exists()
        messages = list(get_messages(response.wsgi_request))
        assert any(message.message == "You do not have rights to remove this challenge." for message in messages)

    def test_delete_challenge_view_unauthenticated(self, client, challenge):
        url = reverse('delete-challenge', args=[challenge.pk])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))