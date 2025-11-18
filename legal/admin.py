
from django.contrib import admin
from .models import LegalDocument

@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
	list_display = ('title', 'is_active', 'last_updated')
	search_fields = ('title',)
