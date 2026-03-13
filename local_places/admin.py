from django import forms
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip, OperatingHours
from unfold.admin import ModelAdmin, TabularInline


from django.core.exceptions import ValidationError


class OperatingHoursFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        selected_days = []
        for form in self.forms:
            # Skip forms marked for deletion
            if self.can_delete and self._should_delete_form(form):
                continue

            day = form.cleaned_data.get("day_of_week")

            # Form might be empty / incomplete
            if day is None:
                continue

            if day in selected_days:
                form.add_error("day_of_week", "This day is already selected.")
                raise ValidationError(
                    "You cannot add operating hours for the same day multiple times."
                )

            selected_days.append(day)


class OperatingHoursInline(TabularInline):
    model = OperatingHours
    formset = OperatingHoursFormSet
    extra = 0
    max_num = 7
    fields = ("day_of_week", "open_time", "close_time", "is_closed")
    ordering = ("day_of_week",)


@admin.register(LocalPlace)
class LocalPlaceAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = (
        "name",
        "category",
        "popularity_score",
        "review_count",
        "address",
        "website_url",
        "contact_number",
        "is_active",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("category", "is_active")
    inlines = [OperatingHoursInline]

    @property
    def media(self):
        api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        extra_js = forms.Media(
            js=[
                f"https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places",
                "local_places/js/admin_places.js",
            ]
        )
        return super().media + extra_js


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
