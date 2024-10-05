from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from .models import BlacklistedUsername, ProductRoleAssignment, SignInAttempt, SignUpRequest, User, OrganisationPersonRoleAssignment

admin.site.register(
    [
        SignInAttempt,
        SignUpRequest,
    ]
)

@admin.register(BlacklistedUsername)
class BlacklistedUsernameAdmin(admin.ModelAdmin):
    list_display = ['username']
    search_fields = ['username']

@admin.register(ProductRoleAssignment)
class ProductRoleAssignmentAdmin(admin.ModelAdmin):
    def product_name(self, obj):
        return obj.product.name

    def person_name(self, obj):
        return obj.person.user

    list_display = ["pk", "product_name", "person_name", "role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "product__name",
    ]

@admin.register(OrganisationPersonRoleAssignment)
class OrganisationPersonRoleAssignmentAdmin(admin.ModelAdmin):
    def organisation_name(self, obj):
        return obj.organisation.name

    def person_name(self, obj):
        return obj.person.user

    list_display = ["pk", "organisation_name", "person_name", "role"]
    search_fields = [
        "person__user__username",
        "person__user__email",
        "organisation__name",
    ]

@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    list_display = ["pk", "first_name", "last_name", "username", "is_test_user"]
    search_fields = ["pk", "first_name", "last_name", "username"]
    list_filter = auth_admin.UserAdmin.list_filter + ("is_test_user",)

# Update the Meta class in your models to fix pluralization
BlacklistedUsername._meta.verbose_name_plural = "Blacklisted Usernames"