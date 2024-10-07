import pytest
from apps.product_management.models import Challenge, Bounty

@pytest.mark.django_db
class TestChallengeWorkflow:
    def test_challenge_bounty_workflow(self, challenge, bounty):
        assert challenge.status == Challenge.ChallengeStatus.DRAFT
        assert bounty.status == Bounty.BountyStatus.DRAFT

        # Activate the challenge
        challenge.status = Challenge.ChallengeStatus.ACTIVE
        challenge.save()

        # Publish the bounty
        bounty.status = Bounty.BountyStatus.OPEN
        bounty.save()
        assert bounty.status == Bounty.BountyStatus.OPEN

        # Complete the bounty
        bounty.status = Bounty.BountyStatus.COMPLETED
        bounty.save()
        challenge.refresh_from_db()
        assert challenge.status == Challenge.ChallengeStatus.COMPLETED

    def test_challenge_multiple_bounties(self, challenge, bounty):
        challenge.status = Challenge.ChallengeStatus.ACTIVE
        challenge.save()

        bounty2 = Bounty.objects.create(
            challenge=challenge,
            title='Test Bounty 2',
            reward_amount=200,
            reward_type='USD'
        )

        bounty.status = Bounty.BountyStatus.COMPLETED
        bounty.save()
        challenge.refresh_from_db()
        assert challenge.status == Challenge.ChallengeStatus.ACTIVE

        bounty2.status = Bounty.BountyStatus.COMPLETED
        bounty2.save()
        challenge.refresh_from_db()
        assert challenge.status == Challenge.ChallengeStatus.COMPLETED