from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.fields import Base58UUIDv5Field
from apps.common.mixins import TimeStampMixin


class Notification(TimeStampMixin):
    id = Base58UUIDv5Field(primary_key=True)
    class EventType(models.TextChoices):
        BOUNTY_CREATED = 'BOUNTY_CREATED', _("Bounty Created")
        BOUNTY_CLAIMED = 'BOUNTY_CLAIMED', _("Bounty Claimed")
        BOUNTY_COMPLETED = 'BOUNTY_COMPLETED', _("Bounty Completed")
        BOUNTY_AWARDED = 'BOUNTY_AWARDED', _("Bounty Awarded")
        CHALLENGE_STARTED = 'CHALLENGE_STARTED', _("Challenge Started")
        CHALLENGE_COMPLETED = 'CHALLENGE_COMPLETED', _("Challenge Completed")
        COMPETITION_OPENED = 'COMPETITION_OPENED', _("Competition Opened")
        COMPETITION_CLOSED = 'COMPETITION_CLOSED', _("Competition Closed")
        ENTRY_SUBMITTED = 'ENTRY_SUBMITTED', _("Entry Submitted")
        WINNER_ANNOUNCED = 'WINNER_ANNOUNCED', _("Winner Announced")
        ORDER_PLACED = 'ORDER_PLACED', _("Order Placed")
        PAYMENT_RECEIVED = 'PAYMENT_RECEIVED', _("Payment Received")
        FUNDS_ADDED = 'FUNDS_ADDED', _("Funds Added to Wallet")
        POINTS_TRANSFERRED = 'POINTS_TRANSFERRED', _("Points Transferred")
        PRODUCT_MADE_PUBLIC = 'PRODUCT_MADE_PUBLIC', _("Product Made Public")

    event_type = models.CharField(max_length=30, choices=EventType.choices)
    permitted_params = models.CharField(max_length=500)

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_event_type_display()


class EmailNotification(Notification):
    title = models.CharField(max_length=400)
    template = models.CharField(max_length=4000)

    def clean(self):
        _template_is_valid(self.title, self.permitted_params)
        _template_is_valid(self.template, self.permitted_params)


def _template_is_valid(template, permitted_params):
    permitted_params_list = permitted_params.split(",")
    params = {param: "" for param in permitted_params_list}
    try:
        template.format(**params)
    except IndexError:
        raise ValidationError({"template": _("No curly brace without a name permitted")}) from None
    except KeyError as ke:
        raise ValidationError(
            {
                "template": _(
                    f"{ke.args[0]} isn't a permitted param for template. Please use one of these: {permitted_params}"
                )
            }
        ) from None
