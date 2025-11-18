

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from unfold.admin import ModelAdmin




@admin.register(LocalPlace)
class LocalPlaceAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('name', 'category', 'popularity_score', 'is_active', 'created_at')
	search_fields = ('name',)
	list_filter = ('category', 'is_active')


@admin.register(Category)
class CategoryAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('title',)
	search_fields = ('title',)


@admin.register(Tag)
class TagAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('title',)
	search_fields = ('title',)


@admin.register(Activity)
class ActivityAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('title',)
	search_fields = ('title',)


@admin.register(Tip)
class TipAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(StaticMap)
class StaticMapAdmin(ModelAdmin, ImportExportModelAdmin):
	list_display = ('title', 'created_at', 'updated_at')
	search_fields = ('title',)
