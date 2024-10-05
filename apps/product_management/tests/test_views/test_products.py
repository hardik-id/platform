import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from apps.product_management.models import Product, Challenge, ProductArea, Initiative, Idea, Bug, Bounty
from apps.commerce.models import Organisation
from apps.security.models import ProductRoleAssignment
from apps.talent.models import Person

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def person(user):
    return Person.objects.create(user=user)

@pytest.fixture
def product(person):
    return Product.objects.create(name='Test Product', slug='test-product', is_private=False, person=person)

@pytest.fixture
def organisation():
    return Organisation.objects.create(name='Test Organisation')

@pytest.fixture
def products(person):
    return [Product.objects.create(name=f'Product {i}', slug=f'product-{i}', is_private=False, person=person) for i in range(10)]

@pytest.mark.django_db
class TestProductListView:
    def test_product_list_view(self, client, product):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'products' in response.context
        assert product in response.context['products']

    def test_product_list_view_exclude_private(self, client, person):
        private_product = Product.objects.create(name='Private Product', slug='private-product', is_private=True, person=person)
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert private_product not in response.context['products']

    def test_product_list_view_pagination(self, client, products):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'products' in response.context
        assert len(response.context['products']) == 8

        response = client.get(f"{url}?page=2")
        assert 'products' in response.context
        assert len(response.context['products']) == 2

@pytest.mark.django_db
class TestProductRedirectView:
    def test_product_redirect_view(self, client, product):
        url = reverse('product-redirect', args=[product.slug])
        response = client.get(url)
        assert response.status_code == 302
        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse('product_summary', kwargs={'slug': product.slug})

@pytest.mark.django_db
class TestProductSummaryView:
    def test_product_summary_view(self, client, product, user, person):
        Challenge.objects.create(title='Test Challenge', product=product, status=Challenge.ChallengeStatus.ACTIVE)
        ProductRoleAssignment.objects.create(
            person=person,
            product=product,
            role=ProductRoleAssignment.ProductRoles.ADMIN
        )
        url = reverse('product_summary', args=[product.slug])
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert 'product' in response.context
        assert 'challenges' in response.context
        assert len(response.context['challenges']) == 1
        assert 'point_balance' in response.context
        assert 'tree_data' in response.context
        assert response.context['can_modify_product'] == True
        assert isinstance(response.context['tree_data'], list)

@pytest.mark.django_db
class TestCreateProductView:
    def test_create_product_view(self, client, user, person, organisation):
        client.force_login(user)
        url = reverse('create-product')
        data = {
            'name': 'New Product',
            'slug': 'new-product',
            'description': 'Test description',
            'full_description': 'Full test description',
            'organisation': organisation.id,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        product = Product.objects.get(name='New Product')
        assert product.name == data['name']
        assert product.full_description == data['full_description']
        assert product.person == person
        assert ProductRoleAssignment.objects.filter(
            person=person,
            product=product,
            role=ProductRoleAssignment.ProductRoles.ADMIN
        ).exists()

    def test_create_product_view_unauthenticated(self, client):
        url = reverse('create-product')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

@pytest.mark.django_db
class TestUpdateProductView:
    def test_update_product_view(self, client, user, person, product, organisation):
        client.force_login(user)
        url = reverse('update-product', args=[product.id])
        data = {
            'name': 'Updated Product',
            'slug': product.slug,
            'description': 'Updated description',
            'full_description': 'Updated full description',
            'organisation': organisation.id,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        product.refresh_from_db()
        assert product.name == data['name']
        assert product.full_description == data['full_description']
        assert product.person == person

    def test_update_product_view_unauthenticated(self, client, product):
        url = reverse('update-product', args=[product.id])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

@pytest.mark.django_db
class TestCreateOrganisationView:
    def test_create_organisation_view(self, client, user):
        client.force_login(user)
        url = reverse('create-organisation')
        data = {
            'name': 'New Organisation',
            'country': 'US',
            'tax_id': '123456789',
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Organisation.objects.filter(name='New Organisation').exists()

@pytest.mark.django_db
class TestProductIdeasAndBugsView:
    def test_product_ideas_and_bugs_view(self, client, product, user):
        Idea.objects.create(title='Test Idea', product=product, person=user.person)
        Bug.objects.create(title='Test Bug', product=product, person=user.person)
        url = reverse('product-ideas-and-bugs', args=[product.slug])
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert 'ideas' in response.context
        assert 'bugs' in response.context
        assert len(response.context['ideas']) == 1
        assert len(response.context['bugs']) == 1

@pytest.mark.django_db
class TestProductTreeInteractiveView:
    def test_product_tree_interactive_view(self, client, product, user):
        ProductArea.add_root(name='Root Area', product_tree=product.product_trees.create())
        url = reverse('product-tree-interactive', args=[product.slug])
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert 'tree_data' in response.context
        assert len(response.context['tree_data']) == 1

@pytest.mark.django_db
class TestProductInitiativesView:
    def test_product_initiatives_view(self, client, product, user):
        initiative = Initiative.objects.create(name='Test Initiative', product=product)
        challenge = Challenge.objects.create(title='Test Challenge', product=product, initiative=initiative)
        Bounty.objects.create(
            challenge=challenge,
            title='Test Bounty',
            reward_amount=100,
            reward_type=Bounty.RewardType.POINTS,
            status=Bounty.BountyStatus.AVAILABLE
        )
        url = reverse('product-initiatives', args=[product.slug])
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert 'initiatives' in response.context
        assert len(response.context['initiatives']) == 1
        assert response.context['initiatives'][0].total_points == 100

@pytest.mark.django_db
class TestProductSettingView:
    def test_product_setting_view(self, client, user, person, product):
        client.force_login(user)
        url = reverse('product-setting', args=[product.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context
        assert 'product_instance' in response.context
        assert response.context['product_instance'] == product

@pytest.mark.django_db
class TestProductRoleAssignmentView:
    def test_product_role_assignment_view(self, client, user, person, product):
        ProductRoleAssignment.objects.create(
            person=person,
            product=product,
            role=ProductRoleAssignment.ProductRoles.ADMIN
        )
        url = reverse('product-people', args=[product.slug])
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == 200
        assert 'product_people' in response.context
        assert len(response.context['product_people']) == 1