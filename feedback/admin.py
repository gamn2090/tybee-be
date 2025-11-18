
from django.contrib import admin
from .models import UserFeedback

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
	list_display = ('user', 'feedback_type', 'status', 'created_at')
	search_fields = ('user__email', 'feedback_type', 'status')
	list_filter = ('status', 'feedback_type')
