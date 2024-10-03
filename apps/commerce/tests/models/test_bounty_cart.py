import pytest
from django.urls import reverse
from apps.commerce.models import BountyCart, PointTransaction

@pytest.mark.django_db
class TestBountyCartProcessing:
    def test_process_cart_with_points(self, client, user, bounty_cart_with_items, organisation_point_account):
        client.force_login(user)
        bounty_cart_with_items.organisation = organisation_point_account.organisation
        bounty_cart_with_items.save()
        
        initial_balance = organisation_point_account.balance
        total_points = bounty_cart_with_items.total_points()
        
        url = reverse('process_cart', args=[bounty_cart_with_items.id])
        response = client.post(url)
        
        assert response.status_code == 302
        bounty_cart_with_items.refresh_from_db()
        assert bounty_cart_with_items.status == BountyCart.BountyCartStatus.COMPLETED
        
        organisation_point_account.refresh_from_db()
        assert organisation_point_account.balance == initial_balance - total_points
        
        point_transaction = PointTransaction.objects.filter(bounty_cart=bounty_cart_with_items).first()
        assert point_transaction is not None
        assert point_transaction.amount == total_points
        assert point_transaction.transaction_type == 'USE'

    def test_process_cart_with_usd(self, client, user, bounty_cart_with_usd_items):
        client.force_login(user)
        
        url = reverse('process_cart', args=[bounty_cart_with_usd_items.id])
        response = client.post(url)
        
        assert response.status_code == 302
        bounty_cart_with_usd_items.refresh_from_db()
        assert bounty_cart_with_usd_items.status == BountyCart.BountyCartStatus.COMPLETED
        
        # Add assertions to check if USD payment was processed correctly

    def test_process_cart_insufficient_points(self, client, user, bounty_cart_with_items, organisation_point_account):
        client.force_login(user)
        bounty_cart_with_items.organisation = organisation_point_account.organisation
        bounty_cart_with_items.save()
        
        # Set balance to less than required
        organisation_point_account.balance = bounty_cart_with_items.total_points() - 1
        organisation_point_account.save()
        
        url = reverse('process_cart', args=[bounty_cart_with_items.id])
        response = client.post(url)
        
        assert response.status_code == 302  # Assuming it redirects on failure
        bounty_cart_with_items.refresh_from_db()
        assert bounty_cart_with_items.status != BountyCart.BountyCartStatus.COMPLETED
        
        assert PointTransaction.objects.filter(bounty_cart=bounty_cart_with_items).count() == 0