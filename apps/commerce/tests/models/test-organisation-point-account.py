import pytest
from apps.commerce.models import OrganisationPointAccount, ProductPointAccount, PointTransaction

@pytest.mark.django_db
class TestOrganisationPointAccount:
    @pytest.fixture
    def point_account(self, organisation):
        return OrganisationPointAccount.objects.create(organisation=organisation, balance=1000)

    def test_create_point_account(self, point_account):
        assert point_account.balance == 1000
        assert str(point_account) == f"Point Account for {point_account.organisation.name}"

    def test_add_points(self, point_account):
        point_account.add_points(500)
        assert point_account.balance == 1500

    def test_use_points(self, point_account):
        assert point_account.use_points(500)
        assert point_account.balance == 500
        assert not point_account.use_points(1000)
        assert point_account.balance == 500

    def test_transfer_points_to_product(self, point_account, product):
        product_account = ProductPointAccount.objects.create(product=product, balance=0)
        assert point_account.transfer_points_to_product(product, 500)
        assert point_account.balance == 500
        assert product_account.balance == 500

        transaction = PointTransaction.objects.first()
        assert transaction.account == point_account
        assert transaction.product_account == product_account
        assert transaction.amount == 500
        assert transaction.transaction_type == 'TRANSFER'
