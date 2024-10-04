import pytest
from apps.commerce.models import ProductPointAccount

@pytest.mark.django_db
class TestProductPointAccount:
    @pytest.fixture
    def product_point_account(self, product):
        return ProductPointAccount.objects.create(product=product, balance=1000)

    def test_create_product_point_account(self, product_point_account):
        assert product_point_account.balance == 1000
        assert str(product_point_account) == f"Point Account for {product_point_account.product.name}"

    def test_add_points(self, product_point_account):
        product_point_account.add_points(500)
        assert product_point_account.balance == 1500

    def test_use_points(self, product_point_account):
        assert product_point_account.use_points(500)
        assert product_point_account.balance == 500
        assert not product_point_account.use_points(1000)
        assert product_point_account.balance == 500
