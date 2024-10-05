from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from apps.product_management import models as product


@admin.register(product.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["slug", "name", "organisation", "is_private"]
    list_filter = ["is_private"]
    search_fields = ["slug", "name", "organisation__name"]
    filter_horizontal = ("attachments",)


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