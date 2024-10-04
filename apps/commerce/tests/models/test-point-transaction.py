import pytest
from apps.commerce.models import PointTransaction, OrganisationPointAccount, ProductPointAccount

@pytest.mark.django_db
class TestPointTransaction:
    @pytest.fixture
    def org_point_account(self, organisation):
        return OrganisationPointAccount.objects.create(organisation=organisation, balance=1000)

    @pytest.fixture
    def product_point_account(self, product):
        return ProductPointAccount.objects.create(product=product, balance=1000)

    def test_create_org_transaction(self, org_point_account):
        transaction = PointTransaction.objects.create(
            account=org_point_account,
            amount=500,
            transaction_type='GRANT',
            description='Test grant'
        )
        assert str(transaction) == f"Grant of 500 points for {org_point_account.organisation.name}"

    def test_create_product_transaction(self, product_point_account):
        transaction = PointTransaction.objects.create(
            product_account=product_point_account,
            amount=500,
            transaction_type='USE',
            description='Test use'
        )
        assert str(transaction) == f"Use of 500 points for {product_point_account.product.name}"

    def test_invalid_transaction(self, org_point_account, product_point_account):
        with pytest.raises(ValueError):
            PointTransaction.objects.create(
                account=org_point_account,
                product_account=product_point_account,
                amount=500,
                transaction_type='TRANSFER',
                description='Invalid transaction'
            )
