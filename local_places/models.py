import requests
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from tybee_backend.validators import (
    validate_image_size,
    validate_image_extension,
    validate_pdf_extension,
)


class CartMap(models.Model):
    MAP_FILE_TYPE_CHOICES = [
        ("image", "Image"),
        ("pdf", "PDF"),
    ]
    map_file_type = models.CharField(
        max_length=10, choices=MAP_FILE_TYPE_CHOICES, default="image"
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="cart_maps/",
        validators=[validate_image_extension, validate_image_size],
        null=True,
        blank=True,
    )
    pdf = models.FileField(
        upload_to="cart_maps/pdfs/",
        validators=[validate_pdf_extension, validate_image_size],
        null=True,
        blank=True,
    )
    description = CKEditor5Field("Description", config_name="extends")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.map_file_type == "image" and not self.image:
            raise ValidationError(
                {"image": "Please upload an image for this Cart Map."}
            )
        if self.map_file_type == "pdf" and not self.pdf:
            raise ValidationError({"pdf": "Please upload a PDF for this Cart Map."})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Cart Map"
        verbose_name_plural = "Cart Maps"


class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive categories, and the places under them, are hidden from the app.",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Tag(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title


class Activity(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="activities")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"


class LiveLikeALocal(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="live_like_a_local")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Live Like a Local"
        verbose_name_plural = "Live Like a Local"


class LocalPlaceImage(models.Model):
    local_place = models.ForeignKey(
        "LocalPlace", on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(
        upload_to="local_places/",
        validators=[validate_image_extension, validate_image_size],
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Local Place Image"
        verbose_name_plural = "Local Place Images"

    def clean(self):
        from django.core.exceptions import ValidationError

        local_place_id = getattr(self, 'local_place_id', None)
        if not self.pk and local_place_id is not None:
            count = LocalPlaceImage.objects.filter(local_place_id=local_place_id).count()
            if count >= 10:
                raise ValidationError("A maximum of 10 images can be added per place.")

    def __str__(self):
        return f"Image for {self.local_place.name}"


class LocalPlace(models.Model):
    name = models.CharField(max_length=255)
    description = CKEditor5Field("Description", config_name="extends")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="places",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="places")
    activities = models.ManyToManyField(Activity, blank=True, related_name="places")
    live_like_a_local = models.ManyToManyField(
        LiveLikeALocal, blank=True, related_name="places"
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    popularity_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.IntegerField(default=0, null=True, blank=True)
    google_places_id = models.CharField(max_length=255, blank=True, null=True)
    google_places_link = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=500)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Local Place"
        verbose_name_plural = "Local Places"


class OperatingHours(models.Model):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]
    local_place = models.ForeignKey(
        LocalPlace, on_delete=models.CASCADE, related_name="operating_hours"
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["day_of_week"]
        unique_together = ("local_place", "day_of_week")
        verbose_name = "Operating Hours"
        verbose_name_plural = "Operating Hours"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Require times if not closed
        if not self.is_closed:
            if not self.open_time or not self.close_time:
                raise ValidationError("Please provide both opening and closing times, or mark as closed.")
                
        local_place_id = getattr(self, 'local_place_id', None)

        # Check if 7 days are already filled up
        if not self.pk and local_place_id is not None:
            count = OperatingHours.objects.filter(local_place_id=local_place_id).count()
            if count >= 7:
                raise ValidationError(
                    "A maximum of 7 operating hours can be added per place."
                )

            # Additional check to absolutely ensure day is unique before saving
            if OperatingHours.objects.filter(
                local_place_id=local_place_id, day_of_week=self.day_of_week
            ).exists():
                raise ValidationError(
                    f"{self.get_day_of_week_display()} is already added for this place."
                )

    def __str__(self):
        return f"{self.local_place.name} — {self.get_day_of_week_display()}"


# Trigger reload
