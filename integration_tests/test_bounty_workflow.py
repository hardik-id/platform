import pytest
from django.utils import timezone
from apps.product_management.models import Bounty
from apps.talent.models import Person, BountyBid, BountyClaim

@pytest.mark.django_db
class TestBountyWorkflow:
    def test_bounty_bid_claim_workflow(self, bounty, person):
        # Open the bounty
        bounty.status = Bounty.BountyStatus.OPEN
        bounty.save()
        assert bounty.status == Bounty.BountyStatus.OPEN

        # Create a bid
        bid = BountyBid.objects.create(
            bounty=bounty,
            person=person,
            amount=100,
            expected_finish_date=timezone.now().date() + timezone.timedelta(days=7)
        )
        assert bid.status == BountyBid.Status.PENDING
        
        # Accept the bid
        bid.status = BountyBid.Status.ACCEPTED
        bid.save()
        bounty.refresh_from_db()
        assert bounty.status == Bounty.BountyStatus.IN_PROGRESS

        # Create a claim
        claim = BountyClaim.objects.create(
            bounty=bounty,
            person=person,
            accepted_bid=bid
        )
        assert claim.status == BountyClaim.Status.ACTIVE

        # Complete the claim
        claim.status = BountyClaim.Status.COMPLETED
        claim.save()
        bounty.refresh_from_db()
        assert bounty.status == Bounty.BountyStatus.COMPLETED

    def test_failed_claim_workflow(self, bounty, person):
        bounty.status = Bounty.BountyStatus.OPEN
        bounty.save()

        bid = BountyBid.objects.create(
            bounty=bounty,
            person=person,
            amount=100,
            expected_finish_date=timezone.now().date() + timezone.timedelta(days=7)
        )
        bid.status = BountyBid.Status.ACCEPTED
        bid.save()

        claim = BountyClaim.objects.create(
            bounty=bounty,
            person=person,
            accepted_bid=bid
        )

        # Fail the claim
        claim.status = BountyClaim.Status.FAILED
        claim.save()
        bounty.refresh_from_db()
        assert bounty.status == Bounty.BountyStatus.OPEN

    def test_multiple_bids_workflow(self, bounty, person):
        bounty.status = Bounty.BountyStatus.OPEN
        bounty.save()

        # Create multiple bids
        bid1 = BountyBid.objects.create(
            bounty=bounty,
            person=person,
            amount=100,
            expected_finish_date=timezone.now().date() + timezone.timedelta(days=7)
        )
        bid2 = BountyBid.objects.create(
            bounty=bounty,
            person=Person.objects.create(user=get_user_model().objects.create_user(username='testuser2'), full_name='Test Person 2'),
            amount=90,
            expected_finish_date=timezone.now().date() + timezone.timedelta(days=6)
        )

        assert BountyBid.objects.filter(bounty=bounty).count() == 2

        # Accept one bid
        bid1.status = BountyBid.Status.ACCEPTED
        bid1.save()
        bounty.refresh_from_db()
        assert bounty.status == Bounty.BountyStatus.IN_PROGRESS

        # Check that other bid is automatically rejected
        bid2.refresh_from_db()
        assert bid2.status == BountyBid.Status.REJECTED