import pytest
from django.utils import timezone
from apps.product_management.models import Competition, Bounty

@pytest.mark.django_db
class TestCompetitionWorkflow:
    def test_competition_workflow(self, competition, bounty):
        assert competition.status == Competition.CompetitionStatus.DRAFT

        # Activate the competition
        competition.status = Competition.CompetitionStatus.ACTIVE
        competition.save()

        # Associate bounty with competition
        bounty.competition = competition
        bounty.save()

        # Close entries
        competition.entry_deadline = timezone.now()
        competition.save()
        competition.refresh_from_db()
        assert competition.status == Competition.CompetitionStatus.ENTRIES_CLOSED

        # Start judging
        competition.judging_deadline = timezone.now() + timezone.timedelta(days=1)
        competition.save()
        competition.refresh_from_db()
        assert competition.status == Competition.CompetitionStatus.JUDGING

        # Complete the competition
        competition.judging_deadline = timezone.now()
        competition.save()
        competition.refresh_from_db()
        assert competition.status == Competition.CompetitionStatus.COMPLETED

        # Verify that associated bounties are completed
        bounty.status = Bounty.BountyStatus.COMPLETED
        bounty.save()
        competition.refresh_from_db()
        assert competition.status == Competition.CompetitionStatus.COMPLETED

    def test_competition_cancellation(self, competition):
        competition.status = Competition.CompetitionStatus.ACTIVE
        competition.save()

        competition.status = Competition.CompetitionStatus.CANCELLED
        competition.save()
        assert competition.status == Competition.CompetitionStatus.CANCELLED

        # Ensure cancelled competitions can't be reactivated
        with pytest.raises(ValidationError):
            competition.status = Competition.CompetitionStatus.ACTIVE
            competition.save()