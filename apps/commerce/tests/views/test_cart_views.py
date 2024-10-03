import pytest
from django.urls import reverse
from apps.commerce.models import BountyCart, BountyCartItem

@pytest.mark.django_db
class TestBountyCartViews:
    def test_create_bounty_cart_view(self, client, user, product):
        client.force_login(user)
        url = reverse('create_bounty_cart')
        response = client.post(url, {'product': product.id})
        assert response.status_code == 302
        assert BountyCart.objects.count() == 1

    def test_add_item_to_cart_view(self, client, user, bounty_cart, bounty):
        client.force_login(user)
        url = reverse('add_to_cart', args=[bounty.id])
        response = client.post(url)
        assert response.status_code == 302
        assert BountyCartItem.objects.count() == 1

    def test_process_cart_view(self, client, user, bounty_cart_with_items, organisation_point_account):
        client.force_login(user)
        bounty_cart_with_items.organisation = organisation_point_account.organisation
        bounty_cart_with_items.save()
        url = reverse('process_cart', args=[bounty_cart_with_items.id])
        response = client.post(url)
        assert response.status_code == 302
        bounty_cart_with_items.refresh_from_db()
        assert bounty_cart_with_items.status == BountyCart.BountyCartStatus.COMPLETED

    def test_cancel_cart_view(self, client, user, bounty_cart_with_items):
        client.force_login(user)
        url = reverse('cancel_cart', args=[bounty_cart_with_items.id])
        response = client.post(url)
        assert response.status_code == 302
        bounty_cart_with_items.refresh_from_db()
        assert bounty_cart_with_items.status == BountyCart.BountyCartStatus.CANCELLED