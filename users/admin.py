
from unfold.admin import ModelAdmin
from django.contrib import admin
from .models import User, PasswordResetOTP

@admin.register(User)
class UserAdmin(ModelAdmin):
	list_display = ('email', 'first_name', 'last_name', 'is_active', 'social_provider', 'date_joined')
	search_fields = ('email', 'first_name', 'last_name')
	list_filter = ('is_active', 'social_provider')

@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(ModelAdmin):
	list_display = ('user', 'otp_code', 'expires_at', 'is_used')
	search_fields = ('user__email', 'otp_code')
