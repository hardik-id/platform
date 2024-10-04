import pytest
from django.utils import timezone
from apps.commerce.models import PlatformFeeConfiguration

@pytest.mark.django_db
class TestPlatformFeeConfiguration:
    def test_create_platform_fee_configuration(self, platform_fee_configuration):
        assert platform_fee_configuration.percentage == 10
        assert platform_fee_configuration.percentage_decimal == 0.10
        assert str(platform_fee_configuration) == f"10% Platform Fee (from {platform_fee_configuration.applies_from_date})"

    def test_get_active_configuration(self, platform_fee_configuration):
        active_config = PlatformFeeConfiguration.get_active_configuration()
        assert active_config == platform_fee_configuration

        future_config = PlatformFeeConfiguration.objects.create(
            percentage=15,
            applies_from_date=timezone.now() + timezone.timedelta(days=1)
        )
        assert PlatformFeeConfiguration.get_active_configuration() == platform_fee_configuration

        past_config = PlatformFeeConfiguration.objects.create(
            percentage=5,
            applies_from_date=timezone.now() - timezone.timedelta(days=1)
        )
        assert PlatformFeeConfiguration.get_active_configuration() == past_config
