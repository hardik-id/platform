from django.contrib import admin
from . import models

admin.site.register([models.Feedback])

@admin.register(models.BountyClaim)
class BountyClaimAdmin(admin.ModelAdmin):
    list_display = [
        "pk",
        "bounty",
        "person",
        "expected_finish_date",
        "status",
    ]
    search_fields = [
        "bounty__title",
        "person__user__username",
        "expected_finish_date",
        "status",
    ]

@admin.register(models.Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "parent"]

@admin.register(models.Expertise)
class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "skill", "fa_icon", "parent"]

@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["pk", "full_name", "user"]

@admin.register(models.PersonSkill)
class PersonSkillAdmin(admin.ModelAdmin):
    list_display = ["pk", "skill", "person"]

@admin.register(models.BountyDeliveryAttempt)
class BountyDeliveryAttemptAdmin(admin.ModelAdmin):
    list_display = ["pk", "status", "bounty_claim", "person",  "delivery_message"]
    list_filter = ["status"]

# Update the Meta classes in your models to fix pluralization
models.BountyClaim._meta.verbose_name_plural = "Bounty Claims"
models.Skill._meta.verbose_name_plural = "Skills"
models.Expertise._meta.verbose_name_plural = "Expertise"
models.PersonSkill._meta.verbose_name_plural = "Person Skills"
models.BountyDeliveryAttempt._meta.verbose_name_plural = "Bounty Delivery Attempts"