from django.conf import settings
from django.db import models, transaction
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
    
    @transaction.atomic
    def transfer_points_to_product(self, product, amount):
        if self.use_points(amount):
            product_account, created = ProductPointAccount.objects.get_or_create(product=product)
            product_account.add_points(amount)
            PointTransaction.objects.create(
                account=self,
                product_account=product_account,
                amount=amount,
                transaction_type='TRANSFER',
                description=f"Transfer from {self.organisation.name} to {product.name}"
            )
            return True
        return False

class ProductPointAccount(TimeStampMixin):
    product = models.OneToOneField('product_management.Product', on_delete=models.CASCADE, related_name='product_point_account')
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Point Account for {self.product.name}"

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
        ('REFUND', 'Refund'),
        ('TRANSFER', 'Transfer')
    ]

    account = models.ForeignKey('OrganisationPointAccount', on_delete=models.CASCADE, related_name='org_transactions', null=True, blank=True)
    product_account = models.ForeignKey('ProductPointAccount', on_delete=models.CASCADE, related_name='product_transactions', null=True, blank=True)
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    sales_order = models.ForeignKey('SalesOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='point_transactions')

    def __str__(self):
        account_name = self.account.organisation.name if self.account else self.product_account.product.name
        return f"{self.get_transaction_type_display()} of {self.amount} points for {account_name}"

    def clean(self):
        if (self.account is None) == (self.product_account is None):
            raise ValidationError("Transaction must be associated with either an OrganisationPointAccount or a ProductPointAccount, but not both.")


class BountyCart(TimeStampMixin, UUIDMixin):
    class BountyCartStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CHECKOUT = "Checkout", "Checkout"
        COMPLETED = "Completed", "Completed"
        ABANDONED = "Abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey('product_management.Product', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=BountyCartStatus.choices,
        default=BountyCartStatus.OPEN
    )

    def __str__(self):
        return f"Bounty Cart for {self.user.username} - {self.product.name} ({self.status})"

    def start_checkout(self):
        if self.status == self.BountyCartStatus.OPEN:
            self.status = self.BountyCartStatus.CHECKOUT
            self.save()
            return SalesOrder.objects.create(
                bounty_cart=self,
                total_points=self.total_points(),
                total_usd=self.total_usd()
            )
        return None

    def total_points(self):
        return sum(item.points for item in self.items.all() if item.bounty.reward_type == 'Points')

    def total_usd(self):
        return sum(item.usd_amount for item in self.items.all() if item.bounty.reward_type == 'USD')


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


class SalesOrder(TimeStampMixin, UUIDMixin):
    class OrderStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAYMENT_PROCESSING = "Payment Processing", "Payment Processing"
        COMPLETED = "Completed", "Completed"
        PAYMENT_FAILED = "Payment Failed", "Payment Failed"
        REFUNDED = "Refunded", "Refunded"

    bounty_cart = models.OneToOneField('BountyCart', on_delete=models.PROTECT, related_name='sales_order')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_points = models.PositiveIntegerField(default=0)
    total_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order {self.id} for Cart {self.bounty_cart.id}"

    @transaction.atomic
    def process_payment(self):
        if self.status != self.OrderStatus.PENDING:
            return False

        self.status = self.OrderStatus.PAYMENT_PROCESSING
        self.save()

        try:
            # Process points
            if self.total_points > 0:
                product_account, created = ProductPointAccount.objects.get_or_create(product=self.bounty_cart.product)
                if not product_account.use_points(self.total_points):
                    raise ValueError("Insufficient points")
                
                PointTransaction.objects.create(
                    product_account=product_account,
                    amount=self.total_points,
                    transaction_type='USE',
                    description=f"Points used for Order {self.id}",
                    bounty_cart=self.bounty_cart
                )

            # Process USD payment
            if self.total_usd > 0:
                if not self._process_usd_payment():
                    raise ValueError("USD payment failed")

            self.status = self.OrderStatus.COMPLETED
            self.save()
            self.activate_purchases()
            self.bounty_cart.status = BountyCart.BountyCartStatus.COMPLETED
            self.bounty_cart.save()
            return True

        except Exception as e:
            self.status = self.OrderStatus.PAYMENT_FAILED
            self.save()
            return False

    def _process_usd_payment(self):
        # Implement USD payment processing logic here
        # Return True if successful, False otherwise
        return True  # Placeholder implementation

    def activate_purchases(self):
        for item in self.bounty_cart.items.all():
            if item.bounty.challenge:
                item.bounty.challenge.status = 'ACTIVE'
                item.bounty.challenge.save()
            # Add similar logic for competitions if needed