
from .models import Rule
from django.contrib import admin
from unfold.admin import ModelAdmin

@admin.register(Rule)
class RuleAdmin(ModelAdmin):
	list_display = ('category', 'title', 'is_active', 'created_at')
	search_fields = ('title', 'category')
	list_filter = ('category', 'is_active')
