from django.conf import settings
from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from apps.openunited.mixins import TimeStampMixin, UUIDMixin
from apps.product_management.models import Challenge, Competition, Bounty, Product

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
        if self.country == "US":
            return self.is_valid_us_ein()
        elif self.country in ["GB", "IE"]:  # UK and Ireland
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
        if self.country == "US":
            return f"EIN: {self.tax_id}"
        elif self.country in ["GB", "IE"]:
            return f"VAT: {self.tax_id}"
        return f"Tax ID: {self.tax_id}"

    def __str__(self):
        return self.name

class OrganisationPointAccount(TimeStampMixin):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name="point_account")
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
                transaction_type="TRANSFER",
                description=f"Transfer from {self.organisation.name} to {product.name}",
            )
            return True
        return False

class ProductPointAccount(TimeStampMixin):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="product_point_account")
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
    TRANSACTION_TYPES = [("GRANT", "Grant"), ("USE", "Use"), ("REFUND", "Refund"), ("TRANSFER", "Transfer")]

    account = models.ForeignKey(
        OrganisationPointAccount, on_delete=models.CASCADE, related_name="org_transactions", null=True, blank=True
    )
    product_account = models.ForeignKey(
        ProductPointAccount, on_delete=models.CASCADE, related_name="product_transactions", null=True, blank=True
    )
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)

    def __str__(self):
        account_name = self.account.organisation.name if self.account else self.product_account.product.name
        return f"{self.get_transaction_type_display()} of {self.amount} points for {account_name}"

    def clean(self):
        if (self.account is None) == (self.product_account is None):
            raise ValidationError(
                "Transaction must be associated with either an OrganisationPointAccount or a ProductPointAccount, but not both."
            )

class OrganisationPointGrant(TimeStampMixin, UUIDMixin):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, related_name="point_grants")
    amount = models.PositiveIntegerField()
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="granted_points"
    )
    rationale = models.TextField()

    def __str__(self):
        return f"Grant of {self.amount} points to {self.organisation.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.organisation.point_account.add_points(self.amount)
        PointTransaction.objects.create(
            account=self.organisation.point_account,
            amount=self.amount,
            transaction_type="GRANT",
            description=f"Grant: {self.rationale}",
        )

class PlatformFeeConfiguration(TimeStampMixin, UUIDMixin):
    percentage = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    applies_from_date = models.DateTimeField()

    @classmethod
    def get_active_configuration(cls):
        return cls.objects.filter(applies_from_date__lte=timezone.now()).order_by("-applies_from_date").first()

    @property
    def percentage_decimal(self):
        return self.percentage / 100

    def __str__(self):
        return f"{self.percentage}% Platform Fee (from {self.applies_from_date})"

    class Meta:
        get_latest_by = "applies_from_date"

class Cart(TimeStampMixin, UUIDMixin):
    class CartStatus(models.TextChoices):
        OPEN = "Open", "Open"
        CHECKOUT = "Checkout", "Checkout"
        COMPLETED = "Completed", "Completed"
        ABANDONED = "Abandoned", "Abandoned"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=CartStatus.choices, default=CartStatus.OPEN)
    user_country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code of the user")

    def __str__(self):
        return f"Cart for {self.user.username} - {self.product.name} ({self.status})"

    def calculate_platform_fee(self):
        usd_items = self.items.filter(funding_type="USD")
        if usd_items.exists():
            config = PlatformFeeConfiguration.get_active_configuration()
            if config:
                total_usd_cents = usd_items.aggregate(total=Sum("funding_amount"))["total"] or 0
                fee_amount_cents = int(total_usd_cents * config.percentage_decimal)
                PlatformFeeCartItem.objects.update_or_create(
                    cart=self,
                    defaults={
                        "amount_cents": fee_amount_cents,
                        "fee_rate": config.percentage_decimal
                    }
                )
                return fee_amount_cents, config.percentage_decimal
        else:
            PlatformFeeCartItem.objects.filter(cart=self).delete()
        return 0, 0

    def calculate_sales_tax(self):
        taxable_amount = self.total_usd_cents()
        
        if self.organisation:
            tax_rate = self.get_organisation_tax_rate()
        elif self.is_user_in_europe():
            tax_rate = self.get_default_european_tax_rate()
        else:
            tax_rate = 0

        tax_amount = int(taxable_amount * tax_rate)
        
        if tax_amount > 0:
            SalesTaxCartItem.objects.update_or_create(
                cart=self,
                defaults={
                    "amount_cents": tax_amount,
                    "tax_rate": tax_rate
                }
            )
        else:
            SalesTaxCartItem.objects.filter(cart=self).delete()

        return tax_amount, tax_rate

    def get_organisation_tax_rate(self):
        # Placeholder implementation
        return 0.2  # 20% tax rate as an example

    def get_default_european_tax_rate(self):
        # Placeholder implementation
        return 0.21  # 21% tax rate as an example

    def is_user_in_europe(self):
        european_countries = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']
        return self.user_country in european_countries

    def total_points(self):
        return sum(item.points for item in self.items.all() if item.bounty.reward_type == "Points")

    def total_usd_cents(self):
        return sum(item.funding_amount for item in self.items.all() if item.bounty.reward_type == "USD")

    @property
    def total_amount_cents(self):
        total = self.items.aggregate(total=Sum("funding_amount"))["total"] or 0
        platform_fee = getattr(self.platform_fee_item, 'amount_cents', 0) if hasattr(self, 'platform_fee_item') else 0
        sales_tax = getattr(self.sales_tax_item, 'amount_cents', 0) if hasattr(self, 'sales_tax_item') else 0
        return total + platform_fee + sales_tax

    @property
    def total_amount(self):
        return self.total_amount_cents / 100

class CartItem(TimeStampMixin, UUIDMixin):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    bounty = models.ForeignKey(Bounty, on_delete=models.CASCADE)
    funding_amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    funding_type = models.CharField(
        max_length=10,
        choices=[("Points", "Points"), ("USD", "USD")],
    )

    def __str__(self):
        return f"Funding for {self.bounty.title} in {self.cart}"

    def clean(self):
        if not self.bounty:
            raise ValidationError("A bounty must be associated with this cart item.")

        if self.funding_type != self.bounty.reward_type:
            raise ValidationError(
                f"Funding type ({self.funding_type}) must match the bounty's reward type ({self.bounty.reward_type})."
            )

        if self.funding_amount != self.bounty.reward_amount:
            raise ValidationError(
                f"Funding amount ({self.funding_amount}) must match the bounty's reward amount ({self.bounty.reward_amount})."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def points(self):
        return self.funding_amount if self.funding_type == "Points" else 0

    @property
    def usd_amount(self):
        return self.funding_amount / 100 if self.funding_type == "USD" else 0

class PlatformFeeCartItem(TimeStampMixin, UUIDMixin):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="platform_fee_item")
    amount_cents = models.PositiveIntegerField()
    fee_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"Platform Fee: ${self.amount_cents/100:.2f} for Cart {self.cart.id}"

class SalesTaxCartItem(TimeStampMixin, UUIDMixin):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="sales_tax_item")
    amount_cents = models.PositiveIntegerField()
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Sales Tax: ${self.amount_cents/100:.2f} for Cart {self.cart.id}"
    
class SalesOrder(TimeStampMixin, UUIDMixin):
    class OrderStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PAYMENT_PROCESSING = "Payment Processing", "Payment Processing"
        COMPLETED = "Completed", "Completed"
        PAYMENT_FAILED = "Payment Failed", "Payment Failed"
        REFUNDED = "Refunded", "Refunded"

    cart = models.OneToOneField(Cart, on_delete=models.PROTECT, related_name="sales_order")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_usd_cents = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Sales Order {self.id} for Cart {self.cart.id}"

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new SalesOrder
            super().save(*args, **kwargs)  # Save first to get a pk
            self.create_line_items()

        self.update_totals()
        super().save(*args, **kwargs)

    def create_line_items(self):
        for cart_item in self.cart.items.filter(funding_type="USD"):
            SalesOrderLineItem.objects.create(
                sales_order=self,
                item_type="BOUNTY",
                bounty=cart_item.bounty,
                quantity=1,
                unit_price_cents=cart_item.funding_amount,
            )

        platform_fee = getattr(self.cart, 'platform_fee_item', None)
        if platform_fee:
            SalesOrderLineItem.objects.create(
                sales_order=self,
                item_type="PLATFORM_FEE",
                quantity=1,
                unit_price_cents=platform_fee.amount_cents,
                fee_rate=platform_fee.fee_rate
            )

        sales_tax = getattr(self.cart, 'sales_tax_item', None)
        if sales_tax:
            SalesOrderLineItem.objects.create(
                sales_order=self,
                item_type="SALES_TAX",
                quantity=1,
                unit_price_cents=sales_tax.amount_cents,
                tax_rate=sales_tax.tax_rate
            )

    def update_totals(self):
        self.total_usd_cents = self.line_items.aggregate(
            total=Sum('unit_price_cents', field="unit_price_cents * quantity")
        )['total'] or 0

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
            self._activate_purchases()
            self.cart.status = Cart.CartStatus.COMPLETED
            self.cart.save()
            return True

        except Exception as e:
            self.status = self.OrderStatus.PAYMENT_FAILED
            self.save()
            return False

    def _process_usd_payment(self):
        # Implement USD payment processing logic here
        # Return True if successful, False otherwise
        return True  # Placeholder implementation

    def _activate_purchases(self):
        for item in self.cart.items.all():
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
        # TODO: Add additional activation logic (e.g., setting start date, notifications)

class SalesOrderLineItem(PolymorphicModel, TimeStampMixin, UUIDMixin):
    sales_order = models.ForeignKey(SalesOrder, related_name="line_items", on_delete=models.CASCADE)
    item_type = models.CharField(
        max_length=20,
        choices=[
            ("BOUNTY", "Bounty"),
            ("PLATFORM_FEE", "Platform Fee"),
            ("SALES_TAX", "Sales Tax"),
        ],
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price_cents = models.PositiveIntegerField()
    bounty = models.ForeignKey(Bounty, on_delete=models.PROTECT, null=True, blank=True)
    fee_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)

    @property
    def total_price_cents(self):
        return self.quantity * self.unit_price_cents

    def __str__(self):
        return f"{self.get_item_type_display()} for Order {self.sales_order.id}"

class PointOrder(TimeStampMixin, UUIDMixin):
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name="point_order")
    product_account = models.ForeignKey(ProductPointAccount, on_delete=models.CASCADE, related_name="point_orders")
    total_points = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("COMPLETED", "Completed"),
            ("REFUNDED", "Refunded"),
        ],
        default="PENDING",
    )

    def __str__(self):
        return f"Point Order of {self.total_points} points for Cart {self.cart.id}"

    @transaction.atomic
    def complete(self):
        if self.status != "PENDING":
            return False

        if self.product_account.use_points(self.total_points):
            self.status = "COMPLETED"
            self.save()
            self._create_point_transactions()
            self._activate_purchases()
            return True
        return False

    @transaction.atomic
    def refund(self):
        if self.status != "COMPLETED":
            return False

        self.product_account.add_points(self.total_points)
        self.status = "REFUNDED"
        self.save()
        self._create_refund_transactions()
        self._deactivate_purchases()
        return True

    def _create_point_transactions(self):
        for item in self.cart.items.filter(funding_type="Points"):
            PointTransaction.objects.create(
                product_account=self.product_account,
                amount=item.funding_amount,
                transaction_type="USE",
                description=f"Points used for Bounty: {item.bounty.title}",
            )

    def _create_refund_transactions(self):
        for item in self.cart.items.filter(funding_type="Points"):
            PointTransaction.objects.create(
                product_account=self.product_account,
                amount=item.funding_amount,
                transaction_type="REFUND",
                description=f"Points refunded for Bounty: {item.bounty.title}",
            )

    def _activate_purchases(self):
        for item in self.cart.items.filter(funding_type="Points"):
            bounty = item.bounty
            if bounty.challenge:
                self._activate_challenge(bounty.challenge)
            elif bounty.competition:
                self._activate_competition(bounty.competition)

    def _deactivate_purchases(self):
        for item in self.cart.items.filter(funding_type="Points"):
            bounty = item.bounty
            if bounty.challenge:
                self._deactivate_challenge(bounty.challenge)
            elif bounty.competition:
                self._deactivate_competition(bounty.competition)

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