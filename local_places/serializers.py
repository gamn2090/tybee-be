from rest_framework import serializers
from .models import (
    LocalPlace,
    CartMap,
    Category,
    Tag,
    Activity,
    LiveLikeALocal,
    OperatingHours,
)
from users.serializers import PresignedUrlField
from datetime import datetime
import pytz

DAY_NAMES = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class OperatingHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = OperatingHours
        fields = (
            "id",
            "day_of_week",
            "day_name",
            "open_time",
            "close_time",
            "is_closed",
        )


class LocalPlaceSerializer(serializers.ModelSerializer):
    image_presigned = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    operating_hours = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    today_timing = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = "__all__"

    def get_operating_hours(self, obj):
        """Return all 7 days — days with no DB row are marked closed."""
        DAY_LABELS = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        hours_by_day = {h.day_of_week: h for h in obj.operating_hours.all()}
        result = []
        for index, label in enumerate(DAY_LABELS):
            row = hours_by_day.get(index)
            result.append(
                {
                    "day_of_week": index,
                    "day_name": label,
                    "open_time": (
                        row.open_time.strftime("%H:%M")
                        if row and row.open_time
                        else None
                    ),
                    "close_time": (
                        row.close_time.strftime("%H:%M")
                        if row and row.close_time
                        else None
                    ),
                    "is_closed": row.is_closed if row else True,
                }
            )
        return result

    def get_image_presigned(self, obj):
        first_image = obj.images.order_by("order", "id").first()
        if first_image and first_image.image:
            pf = PresignedUrlField()
            return pf.to_representation(first_image.image)
        return None

    def get_gallery_images(self, obj):
        """Return a list of pre-signed URLs for all dynamic images."""
        results = []
        for image_obj in obj.images.order_by("order", "id"):
            if image_obj.image:
                pf = PresignedUrlField()
                url = pf.to_representation(image_obj.image)
                if url:
                    results.append(url)
        return results

    def _get_today_hours(self, obj):
        """Return the OperatingHours row for today (EST)."""
        tz = pytz.timezone("America/New_York")
        today_index = datetime.now(tz).weekday()  # 0=Monday
        try:
            return obj.operating_hours.get(day_of_week=today_index)
        except OperatingHours.DoesNotExist:
            return None

    def get_is_open_now(self, obj):
        today = self._get_today_hours(obj)
        if not today or today.is_closed:
            return False
        if not today.open_time or not today.close_time:
            return False
        tz = pytz.timezone("America/New_York")
        now = datetime.now(tz).time()
        return today.open_time <= now < today.close_time

    def get_today_timing(self, obj):
        tz = pytz.timezone("America/New_York")
        now = datetime.now(tz)
        today_index = now.weekday()
        today = self._get_today_hours(obj)
        return {
            "day": DAY_NAMES[today_index],
            "open": (
                today.open_time.strftime("%H:%M") if today and today.open_time else None
            ),
            "close": (
                today.close_time.strftime("%H:%M")
                if today and today.close_time
                else None
            ),
            "is_closed": today.is_closed if today else True,
        }

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def create(self, validated_data):
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = "__all__"


class LiveLikeALocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveLikeALocal
        fields = "__all__"


class CartMapSerializer(serializers.ModelSerializer):
    image_presigned = PresignedUrlField(source="image", read_only=True)
    image_key = serializers.CharField(write_only=True, required=False, allow_null=True)
    pdf_presigned = PresignedUrlField(source="pdf", read_only=True)
    pdf_key = serializers.CharField(write_only=True, required=False, allow_null=True)
    zones = serializers.SerializerMethodField()

    class Meta:
        model = CartMap
        fields = (
            "id",
            "map_file_type",
            "title",
            "image",
            "image_presigned",
            "image_key",
            "pdf",
            "pdf_presigned",
            "pdf_key",
            "description",
            "zones",
            "created_at",
            "updated_at",
        )

    def get_zones(self, obj):
        if obj.title == "Whole Tybee Island":
            # Fetch all other CartMap objects that are "Zones"
            zones = CartMap.objects.filter(title__icontains="Zone").exclude(id=obj.id)
            return [
                {"id": z.id, "title": z.title, "description": z.description}
                for z in zones
            ]
        return []

    def update(self, instance, validated_data):
        image_key = validated_data.pop("image_key", None)
        pdf_key = validated_data.pop("pdf_key", None)
        if image_key:
            validated_data["image"] = image_key
        if pdf_key:
            validated_data["pdf"] = pdf_key
        return super().update(instance, validated_data)

    def create(self, validated_data):
        image_key = validated_data.pop("image_key", None)
        pdf_key = validated_data.pop("pdf_key", None)
        if image_key:
            validated_data["image"] = image_key
        if pdf_key:
            validated_data["pdf"] = pdf_key
        return super().create(validated_data)


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalPlace
        fields = ("id", "name", "latitude", "longitude", "address", "google_places_id")
