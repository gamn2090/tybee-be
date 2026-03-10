from rest_framework import serializers
from .models import Rule, RuleCategory


class RuleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RuleCategory
        fields = ("id", "name", "slug", "is_active")


class RuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Rule
        fields = (
            "id",
            "category",
            "category_name",
            "title",
            "description",
            "is_active",
            "created_at",
        )
