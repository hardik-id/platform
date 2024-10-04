import pytest
from apps.commerce.models import OrganisationPointGrant, PointTransaction

@pytest.mark.django_db
class TestOrganisationPointGrant:
    def test_create_point_grant(self, organisation, user):
        grant = OrganisationPointGrant.objects.create(
            organisation=organisation,
            amount=1000,
            granted_by=user,
            rationale='Test grant'
        )
        assert str(grant) == f"Grant of 1000 points to {organisation.name}"
        assert organisation.point_account.balance == 1000

        transaction = PointTransaction.objects.first()
        assert transaction.account == organisation.point_account
        assert transaction.amount == 1000
        assert transaction.transaction_type == 'GRANT'
        assert transaction.description == 'Grant: Test grant'
