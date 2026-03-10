from django.contrib import admin
from .models import UserFeedback, HelpRequest, ReportProblem, ContactUs
from unfold.admin import ModelAdmin

class ReadOnlyAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UserFeedback)
class UserFeedbackAdmin(ReadOnlyAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(HelpRequest)
class HelpRequestAdmin(ReadOnlyAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(ReportProblem)
class ReportProblemAdmin(ReadOnlyAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)

@admin.register(ContactUs)
class ContactUsAdmin(ReadOnlyAdmin):
    list_display = ('user', 'status', 'created_at')
    search_fields = ('user__email', 'status')
    list_filter = ('status',)
