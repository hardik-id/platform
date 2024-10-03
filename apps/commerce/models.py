from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.openunited.mixins import TimeStampMixin, UUIDMixin

class Organisation(TimeStampMixin):
    name = models.CharField(max_length=512, unique=True)
    country = models.CharField(max_length=2, default='US')  # ISO country code with default 'US'
    vat_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name

class OrganisationPointAccount(TimeStampMixin):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='point_account')
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Point Account for {self.organisation.name}"

    def add_points(self, amount):
        self.balance += amount
        self.save()

    def use_points(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

class PointTransaction(TimeStampMixin, UUIDMixin):
    TRANSACTION_TYPES = [
        ('GRANT', 'Grant'),
        ('USE', 'Use'),
    ]

    account = models.ForeignKey(OrganisationPointAccount, on_delete=models.CASCADE, related_name='transactions')
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    transaction_type = models.CharField(max_length=5, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} points for {self.account.organisation.name}"

class BountyCart(TimeStampMixin, UUIDMixin):
    class BountyCartStatus(models.TextChoices):
        CREATED = "Created", "Created"
        PENDING = "Pending", "Pending Admin Action"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey('product_management.Product', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=BountyCartStatus.choices,
        default=BountyCartStatus.CREATED
    )
    requires_admin_approval = models.BooleanField(default=False)


    def __str__(self):
        return f"Bounty Cart for {self.user.username} - {self.product.name} ({self.status})"

    def total_points(self):
        return sum(item.points for item in self.items.all() if item.bounty.reward_type == 'Points')

    def total_usd(self):
        return sum(item.usd_amount for item in self.items.all() if item.bounty.reward_type == 'USD')

    def process_cart(self):
        if self.status in [self.BountyCartStatus.CREATED, self.BountyCartStatus.PENDING]:
            total_points = self.total_points()
            total_usd = self.total_usd()

            if total_points > 0 and self.organisation:
                if not self.organisation.point_account.use_points(total_points):
                    return False  # Not enough points

            if total_usd > 0:
                # Process USD payment here
                # If payment fails, return False
                pass

            # If we've reached here, both point deduction and USD payment (if applicable) were successful
            for item in self.items.all():
                if item.bounty.challenge:
                    item.bounty.challenge.status = 'ACTIVE'
                    item.bounty.challenge.save()
                # Add similar logic for competitions if needed

            self.status = self.BountyCartStatus.COMPLETED
            self.save()
            return True

        return False

class BountyCartItem(TimeStampMixin, UUIDMixin):
    cart = models.ForeignKey(BountyCart, related_name='items', on_delete=models.CASCADE)
    bounty = models.ForeignKey('product_management.Bounty', on_delete=models.CASCADE)
    points = models.PositiveIntegerField(validators=[MinValueValidator(0)], default=0)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    def __str__(self):
        return f"{self.bounty.title} in {self.cart}"

    def clean(self):
        if self.bounty.reward_type == 'Points' and self.usd_amount > 0:
            raise ValidationError("USD amount should be 0 for Points reward type")
        if self.bounty.reward_type == 'USD' and self.points > 0:
            raise ValidationError("Points should be 0 for USD reward type")
        if self.bounty.reward_type == 'Points' and self.points == 0:
            raise ValidationError("Points should be greater than 0 for Points reward type")
        if self.bounty.reward_type == 'USD' and self.usd_amount == 0:
            raise ValidationError("USD amount should be greater than 0 for USD reward type")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)