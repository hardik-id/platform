import pytest
from apps.commerce.models import OrganisationPointAccount, PointTransaction

@pytest.mark.django_db
class TestOrganisationPointAccount:
    def test_add_points(self, organisation_point_account):
        initial_balance = organisation_point_account.balance
        organisation_point_account.add_points(500)
        assert organisation_point_account.balance == initial_balance + 500

    def test_use_points(self, organisation_point_account):
        initial_balance = organisation_point_account.balance
        assert organisation_point_account.use_points(500) == True
        assert organisation_point_account.balance == initial_balance - 500

    def test_use_points_insufficient_balance(self, organisation_point_account):
        initial_balance = organisation_point_account.balance
        assert organisation_point_account.use_points(initial_balance + 1) == False
        assert organisation_point_account.balance == initial_balance

@pytest.mark.django_db
class TestPointTransaction:
    def test_create_point_transaction(self, organisation_point_account):
        transaction = PointTransaction.objects.create(
            account=organisation_point_account,
            amount=100,
            transaction_type='GRANT',
            description='Test transaction'
        )
        assert transaction.amount == 100
        assert transaction.transaction_type == 'GRANT'
        assert transaction.account == organisation_point_account