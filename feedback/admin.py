from django.contrib import admin
from .models import UserFeedback, HelpRequest, ReportProblem, ContactUs

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(ReportProblem)
class ReportProblemAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)
