
from rest_framework import serializers
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from users.serializers import PresignedUrlField
from datetime import datetime
import pytz


DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

IMAGE_FIELDS = ['image', 'image_2', 'image_3', 'image_4', 'image_5']


class LocalPlaceSerializer(serializers.ModelSerializer):
    image = PresignedUrlField()
    image_2 = PresignedUrlField()
    image_3 = PresignedUrlField()
    image_4 = PresignedUrlField()
    image_5 = PresignedUrlField()
    gallery_images = serializers.SerializerMethodField()
    is_open_now = serializers.SerializerMethodField()
    today_timing = serializers.SerializerMethodField()

    class Meta:
        model = LocalPlace
        fields = '__all__'

    def get_gallery_images(self, obj):
        """Return a list of pre-signed URLs for all non-empty image fields."""
        request = self.context.get('request')
        results = []
        for field_name in IMAGE_FIELDS:
            field = getattr(obj, field_name)
            if field:
                pf = PresignedUrlField()
                pf._name = field_name
                url = pf.to_representation(field)
                if url:
                    results.append(url)
        return results

    def _get_today_hours(self, obj):
        """Return the operating_hours entry for the current day (EST/local)."""
        hours = obj.operating_hours
        if not hours:
            return None
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        today = DAY_NAMES[now.weekday()]  # 0=Monday
        return hours.get(today)

    def get_is_open_now(self, obj):
        today = self._get_today_hours(obj)
        if not today or today.get('is_closed'):
            return False
        open_str = today.get('open')
        close_str = today.get('close')
        if not open_str or not close_str:
            return False
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        try:
            open_t = datetime.strptime(open_str, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day, tzinfo=tz)
            close_t = datetime.strptime(close_str, '%H:%M').replace(
                year=now.year, month=now.month, day=now.day, tzinfo=tz)
            return open_t <= now < close_t
        except ValueError:
            return False

    def get_today_timing(self, obj):
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        today_key = DAY_NAMES[now.weekday()]
        today = self._get_today_hours(obj)
        return {
            'day': today_key,
            'open': today.get('open') if today else None,
            'close': today.get('close') if today else None,
            'is_closed': today.get('is_closed', True) if today else True,
        }


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = '__all__'

class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = '__all__'

class StaticMapSerializer(serializers.ModelSerializer):
    image = PresignedUrlField()
    class Meta:
        model = StaticMap
        fields = '__all__'
