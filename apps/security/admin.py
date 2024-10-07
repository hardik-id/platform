from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.db.models import Case, When, Value, CharField
from django.utils.translation import gettext_lazy as _

from .models import (
    BlacklistedUsername,
    ProductRoleAssignment,
    SignInAttempt,
    SignUpRequest,
    User,
    OrganisationPersonRoleAssignment,
)

admin.site.register([SignInAttempt, SignUpRequest])


@admin.register(BlacklistedUsername)
class BlacklistedUsernameAdmin(admin.ModelAdmin):
    """Admin configuration for BlacklistedUsername model."""

    list_display = ["username"]
    search_fields = ["username"]


@admin.register(ProductRoleAssignment)
class ProductRoleAssignmentAdmin(admin.ModelAdmin):
    """Admin configuration for ProductRoleAssignment model."""

    list_display = ["pk", "product_name", "person_name", "get_role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "product__name",
    ]
    list_select_related = ["product", "person__user"]

    @admin.display(description=_("Product"))
    def product_name(self, obj):
        return obj.product.name

    @admin.display(description=_("Person"))
    def person_name(self, obj):
        return obj.person.user

    @admin.display(description=_("Role"), ordering="role_display")
    def get_role(self, obj):
        roles = {
            "Contributor": "Contributor",
            "Manager": "Manager",
            "Admin": "Admin",
            "0": "Contributor",
            "1": "Manager",
            "2": "Admin",
        }
        return roles.get(str(obj.role), "Unknown")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            role_display=Case(
                When(role="Contributor", then=Value("Contributor")),
                When(role="Manager", then=Value("Manager")),
                When(role="Admin", then=Value("Admin")),
                When(role="0", then=Value("Contributor")),
                When(role="1", then=Value("Manager")),
                When(role="2", then=Value("Admin")),
                default=Value("Unknown"),
                output_field=CharField(),
            )
        )


@admin.register(OrganisationPersonRoleAssignment)
class OrganisationPersonRoleAssignmentAdmin(admin.ModelAdmin):
    """Admin configuration for OrganisationPersonRoleAssignment model."""

    list_display = ["pk", "organisation_name", "person_name", "role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "organisation__name",
    ]
    list_select_related = ["organisation", "person__user"]

    @admin.display(description=_("Organisation"))
    def organisation_name(self, obj):
        return obj.organisation.name

    @admin.display(description=_("Person"))
    def person_name(self, obj):
        return obj.person.user


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    """Admin configuration for custom User model."""

    list_display = ["pk", "first_name", "last_name", "username", "is_test_user"]
    search_fields = ["pk", "first_name", "last_name", "username"]
    list_filter = auth_admin.UserAdmin.list_filter + ("is_test_user",)


# Update the Meta class in your models to fix pluralization
BlacklistedUsername._meta.verbose_name_plural = "Blacklisted Usernames"
