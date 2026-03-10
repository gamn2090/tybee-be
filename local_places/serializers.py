from rest_framework import serializers
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip, OperatingHours
from users.serializers import PresignedUrlField
from datetime import datetime
import pytz

IMAGE_FIELDS = ["image", "image_2", "image_3", "image_4", "image_5"]

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
    image_presigned = PresignedUrlField(source="image", read_only=True)
    image_key = serializers.CharField(write_only=True, required=False, allow_null=True)
    image_2 = PresignedUrlField()
    image_3 = PresignedUrlField()
    image_4 = PresignedUrlField()
    image_5 = PresignedUrlField()
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

    def get_gallery_images(self, obj):
        """Return a list of pre-signed URLs for all non-empty image fields."""
        results = []
        for field_name in IMAGE_FIELDS:
            field = getattr(obj, field_name)
            if field:
                pf = PresignedUrlField()
                url = pf.to_representation(field)
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
        image_key = validated_data.pop("image_key", None)
        if image_key:
            validated_data["image"] = image_key
        return super().update(instance, validated_data)

    def create(self, validated_data):
        image_key = validated_data.pop("image_key", None)
        if image_key:
            validated_data["image"] = image_key
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


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = "__all__"


class StaticMapSerializer(serializers.ModelSerializer):
    image_presigned = PresignedUrlField(source="image", read_only=True)
    image_key = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = StaticMap
        fields = "__all__"

    def update(self, instance, validated_data):
        image_key = validated_data.pop("image_key", None)
        if image_key:
            validated_data["image"] = image_key
        return super().update(instance, validated_data)

    def create(self, validated_data):
        image_key = validated_data.pop("image_key", None)
        if image_key:
            validated_data["image"] = image_key
        return super().create(validated_data)
