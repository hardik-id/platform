import pytest
from django.urls import reverse
from apps.commerce.models import OrganisationPointAccount, PointTransaction

@pytest.mark.django_db
class TestOrganisationPointAccountViews:
    def test_view_organisation_point_account(self, client, user, organisation_point_account):
        client.force_login(user)
        url = reverse('organisation_point_account', args=[organisation_point_account.organisation.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'point_account' in response.context

    def test_grant_points_view(self, client, user, organisation_point_account):
        user.is_staff = True
        user.save()
        client.force_login(user)
        url = reverse('grant_points')
        data = {
            'organisation_id': organisation_point_account.organisation.id,
            'amount': 500,
            'description': 'Test grant'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        organisation_point_account.refresh_from_db()
        assert organisation_point_account.balance == 1500  # 1000 initial + 500 granted

    def test_view_point_transactions(self, client, user, organisation_point_account):
        client.force_login(user)
        PointTransaction.objects.create(
            account=organisation_point_account,
            amount=100,
            transaction_type='GRANT',
            description='Test transaction'
        )
        url = reverse('point_transactions', args=[organisation_point_account.organisation.id])
        response = client.get(url)
        assert response.status_code == 200
        assert 'transactions' in response.context