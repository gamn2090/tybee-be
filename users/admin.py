
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import User, PasswordResetOTP

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'email', 'is_active', 'date_joined', 'profile_pic')
    search_fields = ('phone_number', 'first_name', 'last_name', 'email')
    list_filter = ('is_active',)

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(ModelAdmin):
    list_display = ('user', 'otp_code', 'expires_at', 'is_used')
    search_fields = ('user__phone_number', 'otp_code')
