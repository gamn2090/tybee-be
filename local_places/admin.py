from django import forms
from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
# from import_export.admin import ImportExportModelAdmin
from .models import (
    LocalPlace,
    LocalPlaceImage,
    CartMap,
    Category,
    Tag,
    Activity,
    LiveLikeALocal,
    OperatingHours,
)
from unfold.admin import ModelAdmin, TabularInline
from unfold.widgets import UnfoldAdminTimeWidget


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


class LocalPlaceImageFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()

        selected_orders = []
        for form in self.forms:
            # Skip forms marked for deletion
            if self.can_delete and self._should_delete_form(form):
                continue
            
            # Skip empty forms
            if not form.cleaned_data:
                continue

            order = form.cleaned_data.get("order")

            # Form might be empty / incomplete
            if order is None:
                continue

            if order in selected_orders:
                form.add_error("order", "This order number is already assigned to another image.")
                raise ValidationError(
                    "You cannot have multiple images with the same order number for the same place."
                )

            selected_orders.append(order)


class OperatingHoursForm(forms.ModelForm):
    class Meta:
        model = OperatingHours
        fields = "__all__"
        widgets = {
            "open_time": UnfoldAdminTimeWidget(
                attrs={"type": "time", "placeholder": "HH:MM AM/PM"},
            ),
            "close_time": UnfoldAdminTimeWidget(
                attrs={"type": "time", "placeholder": "HH:MM AM/PM"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["open_time"].help_text = (
            "Click the clock icon or enter time (e.g., 09:00 AM)"
        )
        self.fields["close_time"].help_text = (
            "Click the clock icon or enter time (e.g., 05:00 PM)"
        )


class OperatingHoursInline(TabularInline):
    form = OperatingHoursForm
    model = OperatingHours
    formset = OperatingHoursFormSet
    extra = 0
    max_num = 7
    fields = ("day_of_week", "open_time", "close_time", "is_closed")
    ordering = ("day_of_week",)


class LocalPlaceImageInline(TabularInline):
    model = LocalPlaceImage
    formset = LocalPlaceImageFormSet
    extra = 0
    min_num = 1
    validate_min = True
    max_num = 10
    fields = ("image", "image_preview", "order")
    readonly_fields = ("image_preview",)
    ordering = ("order", "id")

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 150px; width: auto; border-radius: 8px;" />',
                obj.image.url,
            )
        return "No image uploaded"

    image_preview.short_description = "Preview"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image":
            formfield.widget.attrs.update(
                {"accept": ".jpg, .jpeg, .png, .webp, .heic, .heif"}
            )
        return formfield


class LocalPlaceAdminForm(forms.ModelForm):
    class Meta:
        model = LocalPlace
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "name" in self.fields:
            self.fields["name"].widget.attrs["autocomplete"] = "new-password"

        readonly_fields = [
            "latitude",
            "longitude",
            "google_places_id",
            "google_places_link",
        ]
        for field in readonly_fields:
            if field in self.fields:
                self.fields[field].widget.attrs["readonly"] = True
                self.fields[field].widget.attrs[
                    "style"
                ] = "pointer-events: none; opacity: 0.7;"


@admin.register(LocalPlace)
class LocalPlaceAdmin(ModelAdmin):
    form = LocalPlaceAdminForm
    list_display = (
        "name",
        "category",
        "popularity_score",
        "review_count",
        "address_truncated",
        "website_url_truncated",
        "contact_number",
        "is_active",
        "created_at",
    )
    search_fields = ("name",)
    list_filter = ("category", "is_active")
    fieldsets = (
        (
            "General Information",
            {"fields": ("name", "category", "description", "is_active")},
        ),
        (
            "Location & Map Details",
            {"fields": ("address", "latitude", "longitude")},
        ),
        (
            "Google & External Links",
            {
                "fields": (
                    "google_places_id",
                    "google_places_link",
                    "website_url",
                    "contact_number",
                )
            },
        ),
        (
            "Popularity & Reviews",
            {"fields": ("popularity_score", "review_count")},
        ),
        (
            "Grouping & Metadata",
            {"fields": ("tags", "activities", "live_like_a_local")},
        ),
    )
    inlines = [LocalPlaceImageInline, OperatingHoursInline]

    @property
    def media(self):
        api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        extra_js = forms.Media(
            js=[
                f"https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places",
                "local_places/js/admin_places.js?v=1",
            ]
        )
        return super().media + extra_js

    def website_url_truncated(self, obj):
        if obj.website_url and len(obj.website_url) > 30:
            return obj.website_url[:27] + "..."
        return obj.website_url

    website_url_truncated.short_description = "Website"

    def address_truncated(self, obj):
        if obj.address and len(obj.address) > 40:
            return obj.address[:37] + "..."
        return obj.address

    address_truncated.short_description = "Address"




@admin.register(Category)
class CategoryAdmin(ModelAdmin):
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
class TagAdmin(ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ("title", "description_truncated")
    search_fields = ("title",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(LiveLikeALocal)
class LiveLikeALocalAdmin(ModelAdmin):
    list_display = ("name", "description_truncated")
    search_fields = ("name",)

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(CartMap)
class CartMapAdmin(ModelAdmin):
    list_display = (
        "title",
        "description_truncated",
        "map_file_type",
        "image_preview_list",
        "pdf_preview_list",
        "created_at",
    )
    readonly_fields = ("image_preview", "pdf_preview")
    search_fields = ("title", "description")
    fieldsets = [
        (None, {"fields": ("title", "description", "map_file_type")}),
        ("Image Upload", {"fields": ("image", "image_preview")}),
        ("PDF Upload", {"fields": ("pdf", "pdf_preview")}),
    ]

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"

    class Media:
        js = ("local_places/js/cart_map_admin.js",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; width: auto; border-radius: 8px;" />',
                obj.image.url,
            )
        return "No image uploaded"

    def pdf_preview(self, obj):
        if obj.pdf:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6; text-decoration: underline;">View PDF</a>',
                obj.pdf.url,
            )
        return "No PDF uploaded"

    def image_preview_list(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; width: auto; border-radius: 4px;" />',
                obj.image.url,
            )
        return "-"

    def pdf_preview_list(self, obj):
        if obj.pdf:
            return format_html('<span style="color: #10b981;">PDF Available</span>')
        return "-"

    image_preview.short_description = "Image Preview"
    pdf_preview.short_description = "PDF Preview"
    image_preview_list.short_description = "Image"
    pdf_preview_list.short_description = "PDF"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image":
            formfield.widget.attrs.update(
                {"accept": ".jpg, .jpeg, .png, .webp, .heic, .heif"}
            )
        elif db_field.name == "pdf":
            formfield.widget.attrs.update({"accept": ".pdf"})
        return formfield

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


# Trigger reload
