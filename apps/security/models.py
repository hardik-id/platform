import hashlib
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db import models

from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.common.mixins import TimeStampMixin

from apps.talent.models import Person

from .constants import DEFAULT_LOGIN_ATTEMPT_BUDGET
from .managers import UserManager
from random import randrange
from .utils import extract_device_info
from django.contrib.auth import get_user_model
from apps.common.fields import Base58UUIDField

def generate_verification_code():
    return str(randrange(100_000, 1_000_000))


class User(AbstractUser, TimeStampMixin):
    id = Base58UUIDField(primary_key=True)
    remaining_budget_for_failed_logins = models.PositiveSmallIntegerField(default=3)
    password_reset_required = models.BooleanField(default=False)
    is_test_user = models.BooleanField(_("Test User"), default=False)

    objects = UserManager()

    def reset_remaining_budget_for_failed_logins(self):
        self.remaining_budget_for_failed_logins = DEFAULT_LOGIN_ATTEMPT_BUDGET
        self.save()

    def update_failed_login_budget_and_check_reset(self):
        self.remaining_budget_for_failed_logins -= 1

        # If no remaining budget, require a password reset
        if self.remaining_budget_for_failed_logins <= 0:
            self.password_reset_required = True

        self.save()

    def __str__(self):
        return f"{self.username}"


class SignUpRequest(TimeStampMixin):
    id = Base58UUIDField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    device_identifier = models.CharField(max_length=64, null=True, blank=True)
    verification_code = models.CharField(max_length=6)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.successful}"

    @classmethod
    def create_signup_request(cls, email, device_info):
        device_identifier = generate_device_identifier(device_info)
        return cls.objects.create(
            email=email, device_identifier=device_identifier, verification_code=generate_verification_code()
        )


class SignInAttempt(TimeStampMixin):
    id = Base58UUIDField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    device_identifier = models.CharField(max_length=64, null=True, blank=True)
    successful = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user if self.user else 'Unknown User'} - {'Successful' if self.successful else 'Failed'}"


class ProductRoleAssignment(TimeStampMixin):
    from apps.product_management.models import Product

    class ProductRoles(models.TextChoices):
        CONTRIBUTOR = "Contributor"
        MANAGER = "Manager"
        ADMIN = "Admin"

    id = Base58UUIDField(primary_key=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default="")
    role = models.CharField(
        max_length=255,
        choices=ProductRoles.choices,
        default=ProductRoles.CONTRIBUTOR,
    )

    def __str__(self):
        return f"{self.person} - {self.role}"


class BlacklistedUsername(models.Model):
    id = Base58UUIDField(primary_key=True)
    username = models.CharField(max_length=30, unique=True, blank=False)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "black_listed_usernames"


class OrganisationPersonRoleAssignment(TimeStampMixin):
    class OrganisationRoles(models.TextChoices):
        OWNER = "Owner"
        MANAGER = "Manager"
        MEMBER = "Member"
    id = Base58UUIDField(primary_key=True)
    person = models.ForeignKey("talent.Person", on_delete=models.CASCADE)
    organisation = models.ForeignKey("commerce.Organisation", on_delete=models.CASCADE)
    role = models.CharField(
        max_length=255,
        choices=OrganisationRoles.choices,
        default=OrganisationRoles.MEMBER,
    )

    class Meta:
        unique_together = ("person", "organisation")

    def __str__(self):
        return f"{self.person} - {self.organisation} - {self.role}"


def generate_device_identifier(device_info):
    # Combine relevant device information
    device_string = f"{device_info['user_agent']}|{device_info['ip_address']}"
    # Create a hash of the device string
    return hashlib.sha256(device_string.encode()).hexdigest()

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    if user is None:
        # Handle the case where the user is not available
        print("Warning: No user passed to log_successful_login.")
        return

    device_info = extract_device_info(request)
    device_identifier = generate_device_identifier(device_info)

    SignInAttempt.objects.create(user=user, device_identifier=device_identifier, successful=True)

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    device_info = extract_device_info(request)
    device_identifier = generate_device_identifier(device_info)

    # Try to find the user by username or email (depending on your authentication method)
    User = get_user_model()
    try:
        user = User.objects.get(username=credentials.get('username'))  # adjust if you use email login
    except User.DoesNotExist:
        user = None  # No user found

    # Log the failed login attempt
    SignInAttempt.objects.create(
        user=user,  # Can be None if user doesn't exist
        device_identifier=device_identifier,
        successful=False
    )

    # If the user exists, update their failed login budget
    if user:
        user.update_failed_login_budget_and_check_reset()