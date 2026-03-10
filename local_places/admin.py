from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from unfold.admin import ModelAdmin


@admin.register(LocalPlace)
class LocalPlaceAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = (
        "name",
        "category",
        "popularity_score",
        "description_truncated",
        "is_active",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("category", "is_active")

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(Category)
class CategoryAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ("title", "description_truncated")
    search_fields = ("title",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(Tag)
class TagAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Activity)
class ActivityAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ("title", "description_truncated")
    search_fields = ("title",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(Tip)
class TipAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ("name", "description_truncated")
    search_fields = ("name",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(StaticMap)
class StaticMapAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ("title", "description_truncated", "created_at", "updated_at")
    search_fields = ("title",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"
