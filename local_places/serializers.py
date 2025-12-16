
from rest_framework import serializers
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from users.serializers import PresignedUrlField


class LocalPlaceSerializer(serializers.ModelSerializer):
    image = PresignedUrlField()
    class Meta:
        model = LocalPlace
        fields = '__all__'

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
