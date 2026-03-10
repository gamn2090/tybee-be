
from rest_framework import serializers
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from users.serializers import PresignedUrlField


class LocalPlaceSerializer(serializers.ModelSerializer):
    image_presigned = PresignedUrlField(source='image', read_only=True)
    image_key = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = LocalPlace
        fields = '__all__'

    def update(self, instance, validated_data):
        image_key = validated_data.pop('image_key', None)
        if image_key:
            validated_data['image'] = image_key
        return super().update(instance, validated_data)

    def create(self, validated_data):
        image_key = validated_data.pop('image_key', None)
        if image_key:
            validated_data['image'] = image_key
        return super().create(validated_data)

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
    image_presigned = PresignedUrlField(source='image', read_only=True)
    image_key = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = StaticMap
        fields = '__all__'

    def update(self, instance, validated_data):
        image_key = validated_data.pop('image_key', None)
        if image_key:
            validated_data['image'] = image_key
        return super().update(instance, validated_data)

    def create(self, validated_data):
        image_key = validated_data.pop('image_key', None)
        if image_key:
            validated_data['image'] = image_key
        return super().create(validated_data)
