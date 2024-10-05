from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from apps.product_management import models as product
from apps.commerce.models import Organisation
from apps.talent.models import Person

@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name", "person", "organisation", "owner_type", "is_private"]
    list_filter = ["is_private"]
    search_fields = ["slug", "name", "person__user__username", "organisation__name"]
    raw_id_fields = ["person", "organisation"]
    filter_horizontal = ("attachments",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('person', 'organisation')

    def owner_type(self, obj):
        owner = obj.get_owner()
        if isinstance(owner, Organisation):
            return "Organisation"
        elif isinstance(owner, Person):
            return "Person"
        else:
            return "Unknown"
    owner_type.short_description = "Owner Type"

class OwnerTypeFilter(admin.SimpleListFilter):
    title = 'Owner Type'
    parameter_name = 'owner_type'

    def lookups(self, request, model_admin):
        return (
            ('person', 'Person'),
            ('organisation', 'Organisation'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'person':
            return queryset.filter(organisation__isnull=True, person__isnull=False)
        if self.value() == 'organisation':
            return queryset.filter(organisation__isnull=False)

# Add OwnerTypeFilter to the list_filter in ProductAdmin
ProductAdmin.list_filter += (OwnerTypeFilter,)

@admin.register(product.Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "status"]
    list_filter = ["status"]
    search_fields = ["name", "product__name"]


@admin.register(product.ProductTree)
class ProductTreeAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "created_at"]
    search_fields = ["name", "product__name"]


@admin.register(product.ProductArea)
class ProductAreaAdmin(TreeAdmin):
    form = movenodeform_factory(product.ProductArea)
    list_display = ["name", "product_tree", "video_link", "path"]
    search_fields = ["name", "video_link"]
    filter_horizontal = ("attachments",)


@admin.register(product.Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "initiative", "status", "priority", "featured"]
    list_filter = ["status", "priority", "featured"]
    search_fields = ["title", "product__name", "initiative__name"]
    filter_horizontal = ["attachments"]


@admin.register(product.Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "status", "entry_deadline", "judging_deadline"]
    list_filter = ["status"]
    search_fields = ["title", "product__name"]
    filter_horizontal = ["attachments"]


@admin.register(product.Bounty)
class BountyAdmin(admin.ModelAdmin):
    list_display = ["title", "challenge", "competition", "status", "reward_type", "reward_amount"]
    list_filter = ["status", "reward_type"]
    search_fields = ["title", "challenge__title", "competition__title"]
    filter_horizontal = ["expertise", "attachments"]


@admin.register(product.CompetitionEntry)
class CompetitionEntryAdmin(admin.ModelAdmin):
    list_display = ["bounty", "submitter", "status", "entry_time"]
    list_filter = ["status"]
    search_fields = ["bounty__title", "submitter__user__username"]


@admin.register(product.CompetitionEntryRating)
class CompetitionEntryRatingAdmin(admin.ModelAdmin):
    list_display = ["entry", "rater", "rating"]
    list_filter = ["rating"]
    search_fields = ["entry__bounty__title", "rater__user__username"]


@admin.register(product.ChallengeDependency)
class ChallengeDependencyAdmin(admin.ModelAdmin):
    list_display = ["preceding_challenge", "subsequent_challenge"]
    search_fields = ["preceding_challenge__title", "subsequent_challenge__title"]


@admin.register(product.ContributorGuide)
class ContributorGuideAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "skill"]
    search_fields = ["title", "product__name", "skill__name"]


@admin.register(product.Idea)
class IdeaAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "person"]
    search_fields = ["title", "product__name", "person__user__username"]


@admin.register(product.Bug)
class BugAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "person"]
    search_fields = ["title", "product__name", "person__user__username"]


@admin.register(product.ProductContributorAgreementTemplate)
class ProductContributorAgreementTemplateAdmin(admin.ModelAdmin):
    list_display = ["title", "product", "effective_date", "created_by"]
    search_fields = ["title", "product__name", "created_by__user__username"]


@admin.register(product.IdeaVote)
class IdeaVoteAdmin(admin.ModelAdmin):
    list_display = ["voter", "idea"]
    search_fields = ["voter__username", "idea__title"]


@admin.register(product.ProductContributorAgreement)
class ProductContributorAgreementAdmin(admin.ModelAdmin):
    list_display = ["agreement_template", "person", "accepted_at"]
    search_fields = ["agreement_template__title", "person__user__username"]


# Register the FileAttachment model if it's not registered elsewhere
admin.site.register(product.FileAttachment)