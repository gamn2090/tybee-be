from .models import Rule, RuleCategory
from django.contrib import admin
from unfold.admin import ModelAdmin


@admin.register(RuleCategory)
class RuleCategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Rule)
class RuleAdmin(ModelAdmin):
    list_display = (
        "category",
        "title",
        "description_truncated",
        "is_active",
        "created_at",
    )
    search_fields = ("title", "category__name")
    list_filter = ("category", "is_active")

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"
