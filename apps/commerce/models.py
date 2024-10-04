from django.conf import settings
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum
from apps.openunited.mixins import TimeStampMixin, UUIDMixin
from apps.product_management.models import Challenge, Competition, Bounty, Product
from django.apps import apps

class Organisation(TimeStampMixin):
    name = models.CharField(max_length=512, unique=True)
    country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    tax_id = models.CharField(max_length=50, blank=True, null=True, help_text="Tax Identification Number")

    def clean(self):
        if self.tax_id:
            self.tax_id = self.tax_id.upper().replace(" ", "")
            if not self.is_valid_tax_id():
                raise ValidationError("Invalid Tax Identification Number for the specified country.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_valid_tax_id(self):
        if self.country == 'US':
            return self.is_valid_us_ein()
        elif self.country in ['GB', 'IE']:  # UK and Ireland
            return self.is_valid_vat_number()
        return True  # Default to True if no specific validation is implemented

    def is_valid_us_ein(self):
        return len(self.tax_id) == 9 and self.tax_id.isdigit()

    def is_valid_vat_number(self):
        country_prefix = self.tax_id[:2]
        number = self.tax_id[2:]
        if country_prefix != self.country:
            return False
        return len(number) >= 5 and number.isalnum()

    def get_tax_id_display(self):
        if self.country == 'US':
            return f"EIN: {self.tax_id}"
        elif self.country in ['GB', 'IE']:
            return f"VAT: {self.tax_id}"
        return f"Tax ID: {self.tax_id}"

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
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_point_account')
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

    account = models.ForeignKey(OrganisationPointAccount, on_delete=models.CASCADE, related_name='org_transactions', null=True, blank=True)
    product_account = models.ForeignKey(ProductPointAccount, on_delete=models.CASCADE, related_name='product_transactions', null=True, blank=True)
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

class OrganisationPointGrant(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name='point_grants')
    amount = models.PositiveIntegerField()
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='granted_points')
    rationale = models.TextField()

    def __str__(self):
        return f"Grant of {self.amount} points to {self.organisation.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.organisation.point_account.add_points(self.amount)
        PointTransaction.objects.create(
            account=self.organisation.point_account,
            amount=self.amount,
            transaction_type='GRANT',
            description=f"Grant: {self.rationale}"
        )

class BountyCart(TimeStampMixin, UUIDMixin):
    class BountyCartStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CHECKOUT = "Checkout", "Checkout"
        COMPLETED = "Completed", "Completed"
        ABANDONED = "Abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
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
            
            # Create SalesOrder for USD items
            usd_total = self.total_usd_cents()
            if usd_total > 0:
                # Use string reference for SalesOrder
                SalesOrder = apps.get_model('commerce', 'SalesOrder')
                SalesOrder.objects.create(
                    bounty_cart=self,
                    total_usd_cents=usd_total
                )
            
            # Create PointOrder for Point items
            point_total = self.total_points()
            if point_total > 0:
                # Use string reference for PointOrder
                PointOrder = apps.get_model('commerce', 'PointOrder')
                PointOrder.objects.create(
                    product_account=self.product.product_point_account,
                    bounty=self.items.filter(funding_type='Points').first().bounty,
                    amount=point_total,
                    bounty_cart=self
                )
            
            return True
        return False

    def total_points(self):
        return sum(item.points for item in self.items.all() if item.bounty.reward_type == 'Points')

    def total_usd_cents(self):
        return sum(item.funding_amount for item in self.items.all() if item.bounty.reward_type == 'USD')
    

class BountyCartItem(TimeStampMixin, UUIDMixin):
    cart = models.ForeignKey(BountyCart, related_name='items', on_delete=models.CASCADE)
    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE)
    funding_amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    funding_type = models.CharField(
        max_length=10,
        choices=[('Points', 'Points'), ('USD', 'USD')],
    )

    def __str__(self):
        return f"Funding for {self.bounty.title} in {self.cart}"

    def clean(self):
        if not self.bounty:
            raise ValidationError("A bounty must be associated with this cart item.")

        if self.funding_type != self.bounty.reward_type:
            raise ValidationError(f"Funding type ({self.funding_type}) must match the bounty's reward type ({self.bounty.reward_type}).")

        if self.funding_amount != self.bounty.reward_amount:
            raise ValidationError(f"Funding amount ({self.funding_amount}) must match the bounty's reward amount ({self.bounty.reward_amount}).")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def points(self):
        return self.funding_amount if self.funding_type == 'Points' else 0

    @property
    def usd_amount(self):
        return self.funding_amount / 100 if self.funding_type == 'USD' else 0


class SalesOrder(TimeStampMixin, UUIDMixin):
    class OrderStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAYMENT_PROCESSING = "Payment Processing", "Payment Processing"
        COMPLETED = "Completed", "Completed"
        PAYMENT_FAILED = "Payment Failed", "Payment Failed"
        REFUNDED = "Refunded", "Refunded"

    bounty_cart = models.OneToOneField(BountyCart, on_delete=models.PROTECT, related_name='sales_order')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_usd_cents = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Order {self.id} for Cart {self.bounty_cart.id}"

    def clean(self):
        calculated_total_usd_cents = self.calculate_total_usd_cents()
        
        if self.total_usd_cents != calculated_total_usd_cents:
            raise ValidationError(f"Total USD cents mismatch. Expected: {calculated_total_usd_cents}, Got: {self.total_usd_cents}")

    def save(self, *args, **kwargs):
        self.total_usd_cents = self.calculate_total_usd_cents()
        self.full_clean()
        super().save(*args, **kwargs)

    def calculate_total_usd_cents(self):
        return self.bounty_cart.items.filter(funding_type='USD').aggregate(Sum('funding_amount'))['funding_amount__sum'] or 0

    @property
    def total_usd(self):
        return self.total_usd_cents / 100

    @transaction.atomic
    def process_payment(self):
        if self.status != self.OrderStatus.PENDING:
            return False

        self.status = self.OrderStatus.PAYMENT_PROCESSING
        self.save()

        try:
            if self.total_usd_cents > 0:
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
            bounty = item.bounty
            if bounty.challenge:
                self._activate_challenge(bounty.challenge)
            elif bounty.competition:
                self._activate_competition(bounty.competition)

    def _activate_challenge(self, challenge):
        if challenge.status != Challenge.ChallengeStatus.ACTIVE:
            challenge.status = Challenge.ChallengeStatus.ACTIVE
            challenge.save()

    def _activate_competition(self, competition):
        if competition.status == Competition.CompetitionStatus.DRAFT:
            competition.status = Competition.CompetitionStatus.ACTIVE
            competition.save()
        # TODO: refine with steps such as:
        # - Setting the start date if it's not already set
        # - Notifications
        # - Creating any additional objects

    def refund(self):
        if self.status != self.OrderStatus.COMPLETED:
            return False

        try:
            with transaction.atomic():
                # Implement USD refund logic here
                
                self.status = self.OrderStatus.REFUNDED
                self.save()

                # Deactivate purchases
                self._deactivate_purchases()

                return True
        except Exception as e:
            # Log the error
            return False

    def _deactivate_purchases(self):
        for item in self.bounty_cart.items.all():
            bounty = item.bounty
            if bounty.challenge:
                self._deactivate_challenge(bounty.challenge)
            elif bounty.competition:
                self._deactivate_competition(bounty.competition)

    def _deactivate_challenge(self, challenge):
        if challenge.status == Challenge.ChallengeStatus.ACTIVE:
            challenge.status = Challenge.ChallengeStatus.DRAFT
            challenge.save()

    def _deactivate_competition(self, competition):
        if competition.status == Competition.CompetitionStatus.ACTIVE:
            competition.status = Competition.CompetitionStatus.DRAFT
            competition.save()


class PointOrder(TimeStampMixin, UUIDMixin):
    product_account = models.ForeignKey(ProductPointAccount, on_delete=models.CASCADE, related_name='point_orders')
    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE, related_name='point_orders')
    bounty_cart = models.OneToOneField(BountyCart, on_delete=models.CASCADE, related_name='point_order')
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
    ], default='PENDING')

    def __str__(self):
        return f"Point Order of {self.amount} points for {self.bounty.title} in Cart {self.bounty_cart.id}"

    @transaction.atomic
    def complete(self):
        if self.status != 'PENDING':
            return False
        
        if self.product_account.use_points(self.amount):
            self.status = 'COMPLETED'
            self.save()
            PointTransaction.objects.create(
                product_account=self.product_account,
                amount=self.amount,
                transaction_type='USE',
                description=f"Points used for Bounty: {self.bounty.title}"
            )
            self._activate_bounty()
            return True
        return False

    @transaction.atomic
    def refund(self):
        if self.status != 'COMPLETED':
            return False
        
        self.product_account.add_points(self.amount)
        self.status = 'REFUNDED'
        self.save()
        PointTransaction.objects.create(
            product_account=self.product_account,
            amount=self.amount,
            transaction_type='REFUND',
            description=f"Points refunded for Bounty: {self.bounty.title}"
        )
        self._deactivate_bounty()
        return True

    def _activate_bounty(self):
        if self.bounty.challenge:
            self._activate_challenge(self.bounty.challenge)
        elif self.bounty.competition:
            self._activate_competition(self.bounty.competition)

    def _deactivate_bounty(self):
        if self.bounty.challenge:
            self._deactivate_challenge(self.bounty.challenge)
        elif self.bounty.competition:
            self._deactivate_competition(self.bounty.competition)

    def _activate_challenge(self, challenge):
        if challenge.status != Challenge.ChallengeStatus.ACTIVE:
            challenge.status = Challenge.ChallengeStatus.ACTIVE
            challenge.save()

    def _activate_competition(self, competition):
        if competition.status == Competition.CompetitionStatus.DRAFT:
            competition.status = Competition.CompetitionStatus.ACTIVE
            competition.save()
        # TODO: Add additional activation logic (e.g., setting start date, notifications)

    def _deactivate_challenge(self, challenge):
        if challenge.status == Challenge.ChallengeStatus.ACTIVE:
            challenge.status = Challenge.ChallengeStatus.DRAFT
            challenge.save()

    def _deactivate_competition(self, competition):
        if competition.status == Competition.CompetitionStatus.ACTIVE:
            competition.status = Competition.CompetitionStatus.DRAFT
            competition.save()
        # TODO: Add additional deactivation logic if needed