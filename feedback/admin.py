from django.contrib import admin
from .models import UserFeedback, HelpRequest, ReportProblem, ContactUs
from unfold.admin import ModelAdmin


class BaseFeedbackAdmin(ModelAdmin):
    list_per_page = 10000

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    readonly_fields = ("user", "user_name", "message", "created_at")

    def user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "Anonymous"

    user_name.short_description = "User Name"


@admin.register(UserFeedback)
class UserFeedbackAdmin(BaseFeedbackAdmin):
    list_display = ("user_name", "message_truncated", "status", "created_at")
    list_editable = ("status",)
    search_fields = ("user__phone_number", "status", "message")
    list_filter = ("status", "created_at")

    def message_truncated(self, obj):
        return (
            obj.message[:50] + "..."
            if obj.message and len(obj.message) > 50
            else obj.message
        )

    message_truncated.short_description = "Message"


@admin.register(HelpRequest)
class HelpRequestAdmin(BaseFeedbackAdmin):
    list_display = ("user_name", "message_truncated", "status", "created_at")
    list_editable = ("status",)
    search_fields = ("user__phone_number", "status", "message")
    list_filter = ("status", "created_at")

    def message_truncated(self, obj):
        return (
            obj.message[:50] + "..."
            if obj.message and len(obj.message) > 50
            else obj.message
        )

    message_truncated.short_description = "Message"


@admin.register(ReportProblem)
class ReportProblemAdmin(BaseFeedbackAdmin):
    list_display = ("user_name", "message_truncated", "status", "created_at")
    list_editable = ("status",)
    search_fields = ("user__phone_number", "status", "message")
    list_filter = ("status", "created_at")

    def message_truncated(self, obj):
        return (
            obj.message[:50] + "..."
            if obj.message and len(obj.message) > 50
            else obj.message
        )

    message_truncated.short_description = "Message"


@admin.register(ContactUs)
class ContactUsAdmin(BaseFeedbackAdmin):
    list_display = ("user_name", "message_truncated", "status", "created_at")
    list_editable = ("status",)
    search_fields = ("user__phone_number", "status", "message")
    list_filter = ("status", "created_at")

    def message_truncated(self, obj):
        return (
            obj.message[:50] + "..."
            if obj.message and len(obj.message) > 50
            else obj.message
        )

    message_truncated.short_description = "Message"
