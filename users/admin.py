from django.utils.html import format_html
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import User, PasswordResetOTP


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_per_page = 10000
    list_display = (
        "full_name",
        "phone_number",
        "zipcode",
        "profile_pic_preview_list",
    )
    readonly_fields = ("profile_pic_preview",)
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "profile_pic",
                    "profile_pic_preview",
                    "first_name",
                    "last_name",
                    "phone_number",
                    "zipcode",
                )
            },
        ),
        # Hidden/Unused technical fields
        # (
        #     "Permissions",
        #     {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        # ),
        # (
        #     "Important dates",
        #     {"fields": ("last_login", "date_joined")},
        # ),
    ]

    def profile_pic_preview(self, obj):
        if obj.profile_pic:
            return format_html(
                '<img src="{}" style="max-height: 200px; width: auto; border-radius: 8px;" />',
                obj.profile_pic.url,
            )
        return "No profile picture"

    def profile_pic_preview_list(self, obj):
        if obj.profile_pic:
            return format_html(
                '<img src="{}" style="max-height: 40px; width: auto; border-radius: 50%;" />',
                obj.profile_pic.url,
            )
        return "-"

    profile_pic_preview.short_description = "Profile Picture Preview"
    profile_pic_preview_list.short_description = "Pic"

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    full_name.short_description = "Name"

    search_fields = ("phone_number", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "is_superuser")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "profile_pic":
            formfield.widget.attrs.update(
                {"accept": ".jpg, .jpeg, .png, .webp, .heic, .heif"}
            )
        return formfield


# Hidden PasswordResetOTP from admin as requested
# @admin.register(PasswordResetOTP)
# class PasswordResetOTPAdmin(ModelAdmin):
#     list_display = ("user", "otp_code", "expires_at", "is_used")
#     search_fields = ("user__phone_number", "otp_code")
