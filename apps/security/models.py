import hashlib
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db import models

from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.openunited.mixins import TimeStampMixin, UUIDMixin

from apps.talent.models import Person

from .constants import DEFAULT_LOGIN_ATTEMPT_BUDGET
from .managers import UserManager


# This model will be used for advanced authentication methods
class User(AbstractUser, TimeStampMixin):
    remaining_budget_for_failed_logins = models.PositiveSmallIntegerField(default=3)
    password_reset_required = models.BooleanField(default=False)
    is_test_user = models.BooleanField(_("Test User"), default=False)

    objects = UserManager()

    def reset_remaining_budget_for_failed_logins(self):
        self.remaining_budget_for_failed_logins = DEFAULT_LOGIN_ATTEMPT_BUDGET
        self.save()

    def update_failed_login_budget_and_check_reset(self):
        self.remaining_budget_for_failed_logins -= 1

        if self.remaining_budget_for_failed_logins == 0:
            self.password_reset_required = True

        self.save()

    def __str__(self):
        return f"{self.username} - {self.remaining_budget_for_failed_logins} - {self.password_reset_required}"


class SignUpRequest(TimeStampMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    device_identifier = models.CharField(max_length=64, null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    region_code = models.CharField(max_length=8, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    verification_code = models.CharField(max_length=6)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.successful}"
    
    @classmethod
    def create_signup_request(cls, email, device_info, location_info):
        device_identifier = generate_device_identifier(device_info)
        return cls.objects.create(
            email=email,
            device_identifier=device_identifier,
            country=location_info.get('country'),
            region_code=location_info.get('region_code'),
            city=location_info.get('city'),
            verification_code=generate_verification_code()
        )


class SignInAttempt(TimeStampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_identifier = models.CharField(max_length=64, null=True, blank=True)
    country = models.CharField(max_length=64, null=True, blank=True)
    region_code = models.CharField(max_length=8, null=True, blank=True)
    city = models.CharField(max_length=128, null=True, blank=True)
    successful = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.region_code} - {self.city} - {self.country}"


class ProductRoleAssignment(TimeStampMixin, UUIDMixin):
    from apps.product_management.models import Product
    
    class ProductRoles(models.TextChoices):
        CONTRIBUTOR = "Contributor"
        MANAGER = "Manager"
        ADMIN = "Admin"

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
    username = models.CharField(max_length=30, unique=True, blank=False)

    def __str__(self):
        return self.username

    class Meta:
        db_table = "black_listed_usernames"


class OrganisationPersonRoleAssignment(TimeStampMixin, UUIDMixin):
    class OrganisationRoles(models.TextChoices):
        OWNER = "Owner"
        MANAGER = "Manager"
        MEMBER = "Member"

    person = models.ForeignKey("talent.Person", on_delete=models.CASCADE)
    organisation = models.ForeignKey("commerce.Organisation", on_delete=models.CASCADE)
    role = models.CharField(
        max_length=255,
        choices=OrganisationRoles.choices,
        default=OrganisationRoles.MEMBER,
    )

    class Meta:
        unique_together = ('person', 'organisation')

    def __str__(self):
        return f"{self.person} - {self.organisation} - {self.role}"
    
def generate_device_identifier(device_info):
    # Combine relevant device information
    device_string = f"{device_info['user_agent']}|{device_info['ip_address']}"
    # Create a hash of the device string
    return hashlib.sha256(device_string.encode()).hexdigest()

def extract_device_info(request):
    return {
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': request.META.get('REMOTE_ADDR', ''),
    }

def extract_location_info(request):
    # You might want to use a geolocation service here
    # For now, we'll return placeholder data
    return {
        'country': 'Unknown',
        'region_code': 'Unknown',
        'city': 'Unknown',
    }
    

#receivers
@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    device_info = extract_device_info(request)
    location_info = extract_location_info(request)
    device_identifier = generate_device_identifier(device_info)
    
    SignInAttempt.objects.create(
        user=user,
        device_identifier=device_identifier,
        country=location_info.get('country'),
        region_code=location_info.get('region_code'),
        city=location_info.get('city'),
        successful=True
    )

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    device_info = extract_device_info(request)
    location_info = extract_location_info(request)
    device_identifier = generate_device_identifier(device_info)
    
    SignInAttempt.objects.create(
        user=User.objects.filter(username=credentials.get('username')).first(),
        device_identifier=device_identifier,
        country=location_info.get('country'),
        region_code=location_info.get('region_code'),
        city=location_info.get('city'),
        successful=False
    )