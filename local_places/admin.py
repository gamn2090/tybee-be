from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import admin
from django.conf import settings
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import path
from django.utils.html import format_html, strip_tags

from import_export import resources
from import_export.admin import ExportMixin

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
from tybee_backend.search_utils import FuzzySearchAdminMixin, fuzzy_match


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


MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


class LocalPlaceImageForm(forms.ModelForm):
    class Meta:
        model = LocalPlaceImage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "image" in self.fields:
            self.fields["image"].label = "Image (max 5 MB)"

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "size") and image.size > MAX_IMAGE_SIZE_BYTES:
            raise ValidationError(
                f"Image size must not exceed {MAX_IMAGE_SIZE_MB} MB. "
                f"Your file is {image.size / (1024 * 1024):.1f} MB."
            )
        return image


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
                form.add_error(
                    "order", "This order number is already assigned to another image."
                )
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
    form = LocalPlaceImageForm
    formset = LocalPlaceImageFormSet
    extra = 0
    min_num = 0
    validate_min = False
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

        if "contact_number" in self.fields:
            self.fields["contact_number"].widget.attrs.update(
                {
                    "maxlength": "10",
                    "pattern": "[0-9]{10}",
                    "title": "Contact number must be exactly 10 digits.",
                    "oninput": "this.value = this.value.replace(/[^0-9]/g, '')",
                }
            )

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

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get("contact_number")

        # If it's empty, we allow it (since it's blank=True, null=True in model)
        if not contact_number:
            return contact_number

        # Strip any accidental whitespace
        contact_number = contact_number.strip()

        if not contact_number.isdigit():
            raise ValidationError("Contact number must contain only numbers.")

        if len(contact_number) != 10:
            raise ValidationError("Contact number must be exactly 10 digits.")

        return contact_number


class HasPhotosFilter(admin.SimpleListFilter):
    """Report filter: list #6 example — 'View all entries without a photograph'."""

    title = "Has Photos"
    parameter_name = "has_photos"

    def lookups(self, request, model_admin):
        return (("yes", "With photos"), ("no", "Without photos"))

    def queryset(self, request, queryset):
        queryset = queryset.annotate(_image_count=Count("images"))
        if self.value() == "yes":
            return queryset.filter(_image_count__gt=0)
        if self.value() == "no":
            return queryset.filter(_image_count=0)
        return queryset


class PopularityStarsFilter(admin.SimpleListFilter):
    """Report filter: list #6 example — 'View all entries with 3-star recommendations'."""

    title = "Popularity (stars)"
    parameter_name = "stars"

    def lookups(self, request, model_admin):
        return (
            ("5", "5 stars"),
            ("4", "4 stars"),
            ("3", "3 stars"),
            ("2", "2 stars"),
            ("1", "1 star"),
            ("0", "Unrated / 0 stars"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        try:
            stars = Decimal(value)
        except InvalidOperation:
            return queryset
        if stars == 0:
            return queryset.filter(Q(popularity_score=0) | Q(popularity_score__isnull=True))
        # Bucket by whole star: e.g. "3" matches 3.0 - 3.9
        return queryset.filter(popularity_score__gte=stars, popularity_score__lt=stars + 1)


class LocalPlaceResource(resources.ModelResource):
    """Powers the 'Export' button (list #6 example — 'View all restaurants
    with all entered details') added via `ExportMixin` below."""

    category = resources.Field(attribute="category__title", column_name="category")

    class Meta:
        model = LocalPlace
        fields = (
            "id",
            "name",
            "category",
            "description",
            "address",
            "contact_number",
            "website_url",
            "google_places_id",
            "google_places_link",
            "popularity_score",
            "review_count",
            "is_active",
            "created_at",
        )
        export_order = fields


@admin.register(LocalPlace)
class LocalPlaceAdmin(FuzzySearchAdminMixin, ExportMixin, ModelAdmin):
    resource_classes = [LocalPlaceResource]
    form = LocalPlaceAdminForm
    list_per_page = 10000
    list_display = (
        "name_display",
        "category",
        "image_count",
        "popularity_score",
        "review_count",
        "address_truncated",
        "website_url_truncated",
        "contact_number",
        "is_active",
        "created_at",
    )
    # Kept non-empty so Django renders the search box; the actual matching
    # logic lives in `get_search_haystack` below (punctuation/typo-tolerant,
    # also matches category/tags/activities, not just the name).
    search_fields = ("name",)
    list_filter = ("category", "is_active", HasPhotosFilter, PopularityStarsFilter)
    autocomplete_fields = ("tags", "activities", "live_like_a_local")

    def get_search_haystack(self, obj):
        return [
            obj.name,
            obj.address,
            obj.contact_number,
            obj.category.title if obj.category else "",
            " ".join(t.title for t in obj.tags.all()),
            " ".join(a.title for a in obj.activities.all()),
        ]

    def get_search_results(self, request, queryset, search_term):
        queryset = queryset.select_related("category").prefetch_related(
            "tags", "activities"
        )
        return super().get_search_results(request, queryset, search_term)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "search-suggestions/",
                self.admin_site.admin_view(self.search_suggestions_view),
                name="local_places_localplace_search_suggestions",
            ),
        ]
        return custom_urls + urls

    def search_suggestions_view(self, request):
        """Backs the dropdown suggestions list under the changelist search box."""
        query = (request.GET.get("q") or "").strip()
        if not query:
            return JsonResponse({"results": []})

        queryset = self.get_queryset(request).select_related("category")
        results = []
        for obj in queryset:
            haystacks = self.get_search_haystack(obj)
            if any(fuzzy_match(query, h, self.fuzzy_search_threshold) for h in haystacks if h):
                results.append(
                    {
                        "id": obj.pk,
                        "name": obj.name,
                        "category": obj.category.title if obj.category else "",
                    }
                )
            if len(results) >= 8:
                break
        return JsonResponse({"results": results})
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
                f"https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places&loading=async",
                "local_places/js/admin_places.js",
            ]
        )
        return super().media + extra_js

    def website_url_truncated(self, obj):
        if obj.website_url and len(obj.website_url) > 30:
            return obj.website_url[:27] + "..."
        return obj.website_url

    website_url_truncated.short_description = "Website"

    def name_display(self, obj):
        if obj.name and len(obj.name) > 40:
            return obj.name[:37] + "..."
        return obj.name

    name_display.short_description = "Name"
    name_display.admin_order_field = "name"

    def image_count(self, obj):
        return obj.images.count()

    image_count.short_description = "Images"

    def address_truncated(self, obj):
        if obj.address and len(obj.address) > 40:
            return obj.address[:37] + "..."
        return obj.address

    address_truncated.short_description = "Address"


@admin.register(Category)
class CategoryAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("title", "description_truncated", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)

    def get_search_haystack(self, obj):
        return [obj.title, obj.description]

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(Tag)
class TagAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("title",)
    search_fields = ("title",)

    def get_search_haystack(self, obj):
        return [obj.title]


@admin.register(Activity)
class ActivityAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    # `tags` shown so it's plain to see there is no functional difference
    # left between how Tags and Activities are matched/searched today.
    list_display = ("title", "description_truncated", "tag_list")
    search_fields = ("title",)
    autocomplete_fields = ("tags",)

    def get_search_haystack(self, obj):
        return [obj.title, obj.description, " ".join(t.title for t in obj.tags.all())]

    def tag_list(self, obj):
        return ", ".join(t.title for t in obj.tags.all()) or "-"

    tag_list.short_description = "Tags"

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(LiveLikeALocal)
class LiveLikeALocalAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
    list_display = ("name", "description_truncated")
    search_fields = ("name",)

    def get_search_haystack(self, obj):
        return [obj.name, obj.description]

    def description_truncated(self, obj):
        return (
            obj.description[:100] + "..."
            if obj.description and len(obj.description) > 100
            else obj.description
        )

    description_truncated.short_description = "Description"


@admin.register(CartMap)
class CartMapAdmin(FuzzySearchAdminMixin, ModelAdmin):
    list_per_page = 10000
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

    def get_search_haystack(self, obj):
        return [obj.title, strip_tags(obj.description)]

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
                {"accept": ".jpg,.jpeg,.png,.webp,.heic,.heif"}
            )
        elif db_field.name == "pdf":
            formfield.widget.attrs.update({"accept": ".pdf"})
        return formfield

    def description_truncated(self, obj):
        plain = strip_tags(obj.description)
        return plain[:100] + "..." if plain and len(plain) > 100 else plain

    description_truncated.short_description = "Description"


# Trigger reload
