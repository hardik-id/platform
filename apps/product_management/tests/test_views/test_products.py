import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import HttpResponseRedirect
from apps.product_management.models import Product, Challenge, ProductArea, Initiative, Idea, Bug
from apps.commerce.models import Organisation
from apps.security.models import ProductRoleAssignment

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def product():
    return Product.objects.create(name='Test Product', slug='test-product', is_private=False)

@pytest.fixture
def organisation():
    return Organisation.objects.create(name='Test Organisation')

@pytest.fixture
def products():
    return [Product.objects.create(name=f'Product {i}', slug=f'product-{i}', is_private=False) for i in range(10)]

@pytest.mark.django_db
class TestProductListView:
    def test_product_list_view(self, client, product):
        url = reverse('product-list')
        response = client.get(url)
        assert response.status_code == 200
        assert 'products' in response.context
        assert product in response.context['products']

    def test_product_list_view_exclude_private(self, client):
        private_product = Product.objects.create(name='Private Product', slug='private-product', is_private=True)
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
    def test_product_summary_view(self, client, product, user):
        Challenge.objects.create(title='Test Challenge', product=product, status=Challenge.ChallengeStatus.ACTIVE)
        ProductRoleAssignment.objects.create(
            person=user.person,
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
    def test_create_product_view(self, client, user, organisation):
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
        assert ProductRoleAssignment.objects.filter(
            person=user.person,
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
    def test_update_product_view(self, client, user, product, organisation):
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

    def test_update_product_view_unauthenticated(self, client, product):
        url = reverse('update-product', args=[product.id])
        response = client.get(url)
        assert response.status_code == 302
        assert response.url.startswith(reverse('sign_in'))

# ... (rest of the test classes remain the same)