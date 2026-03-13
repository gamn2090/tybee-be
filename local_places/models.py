from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from tybee_backend.validators import validate_image_size, validate_image_extension


class StaticMap(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="static_maps/",
        validators=[validate_image_extension, validate_image_size],
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Static Map"
        verbose_name_plural = "Static Maps"


class Category(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

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


class Tip(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="tips")

    def __str__(self):
        return self.name


class LocalPlace(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="local_places/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    image_2 = models.ImageField(
        upload_to="local_places/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    image_3 = models.ImageField(
        upload_to="local_places/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    image_4 = models.ImageField(
        upload_to="local_places/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    image_5 = models.ImageField(
        upload_to="local_places/",
        blank=True,
        null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    highlight = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name="places",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="places")
    activities = models.ManyToManyField(Activity, blank=True, related_name="places")
    tips = models.ManyToManyField(Tip, blank=True, related_name="places")
    latitude = models.FloatField()
    longitude = models.FloatField()
    popularity_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    review_count = models.IntegerField(default=0)
    google_places_id = models.CharField(max_length=255, blank=True)
    google_places_link = models.URLField(blank=True)
    website_url = models.URLField()
    contact_number = models.CharField(max_length=50)
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

        # Check if 7 days are already filled up
        if not self.pk:
            count = OperatingHours.objects.filter(local_place=self.local_place).count()
            if count >= 7:
                raise ValidationError(
                    "A maximum of 7 operating hours can be added per place."
                )

            # Additional check to absolutely ensure day is unique before saving
            if OperatingHours.objects.filter(
                local_place=self.local_place, day_of_week=self.day_of_week
            ).exists():
                raise ValidationError(
                    f"{self.get_day_of_week_display()} is already added for this place."
                )

    def __str__(self):
        return f"{self.local_place.name} — {self.get_day_of_week_display()}"
