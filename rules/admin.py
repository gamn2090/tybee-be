
from .models import Rule, RuleCategory
from django.contrib import admin
from unfold.admin import ModelAdmin


@admin.register(RuleCategory)
class RuleCategoryAdmin(ModelAdmin):
	list_display = ('name', 'slug', 'is_active', 'created_at')
	search_fields = ('name', 'slug')
	list_filter = ('is_active',)
	prepopulated_fields = {'slug': ('name',)}


@admin.register(Rule)
class RuleAdmin(ModelAdmin):
	list_display = ('category', 'title', 'is_active', 'created_at')
	search_fields = ('title', 'category__name')
	list_filter = ('category', 'is_active')
