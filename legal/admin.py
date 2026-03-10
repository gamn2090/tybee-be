from django.contrib import admin
from .models import LegalDocument
from unfold.admin import ModelAdmin

@admin.register(LegalDocument)
class LegalDocumentAdmin(ModelAdmin):
	list_display = ('title', 'is_active', 'last_updated')
	search_fields = ('title',)
