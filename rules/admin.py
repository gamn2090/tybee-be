from .models import Rule, RuleCategory
from django.contrib import admin
from django.utils.html import strip_tags
from unfold.admin import ModelAdmin
from tybee_backend.search_utils import FuzzySearchAdminMixin


@admin.register(RuleCategory)
class RuleCategoryAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}

    def get_search_haystack(self, obj):
        return [obj.name, obj.slug]


@admin.register(Rule)
class RuleAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = (
        "category",
        "title",
        "description_truncated",
        "is_active",
        "created_at",
    )
    search_fields = ("title", "category__name")
    list_filter = ("category", "is_active")

    def get_search_haystack(self, obj):
        return [
            obj.title,
            strip_tags(obj.description),
            obj.category.name if obj.category else "",
        ]

    def description_truncated(self, obj):
        plain = strip_tags(obj.description)
        return plain[:100] + "..." if plain and len(plain) > 100 else plain

    description_truncated.short_description = "Description"
