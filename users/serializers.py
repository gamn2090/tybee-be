from rest_framework import serializers
from .models import User, PasswordResetOTP, signupOTP
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.core.files.storage import default_storage
import boto3


# Reusable field for presigned S3 URLs (read-only)
class PresignedUrlField(serializers.ReadOnlyField):
    def to_representation(self, value):
        if not value:
            return None
        url = value.url
        if hasattr(default_storage, "bucket"):
            region = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=region,
                endpoint_url=f"https://s3.{region}.amazonaws.com",
            )
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            key = value.name
            try:
                presigned_url = s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket_name, "Key": key},
                    ExpiresIn=3600,
                )
                return presigned_url
            except Exception:
                return url
        return url


class UserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )
    profile_pic_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text="S3 object key from a direct presigned URL upload.",
    )
    profile_pic_presigned = PresignedUrlField(source="profile_pic", read_only=True)
    phone_number = serializers.CharField(
        read_only=True
    )  # Phone number cannot be changed after signup

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "zipcode",
            "is_active",
            "date_joined",
            "profile_pic",
            "profile_pic_key",
            "profile_pic_presigned",
        )
        extra_kwargs = {
            "is_active": {"read_only": True},  # Cannot be changed via profile update
            "date_joined": {"read_only": True},  # Cannot be changed via profile update
        }

    def validate_profile_pic(self, value):
        if value is None:
            return value
        # Enforce 5 MB size limit
        max_size = getattr(settings, "MAX_UPLOAD_FILE_SIZE", 5 * 1024 * 1024)
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size {value.size / (1024 * 1024):.1f} MB exceeds the maximum allowed size of {max_size / (1024 * 1024):.0f} MB."
            )
        # Enforce allowed content types
        allowed_types = getattr(settings, "ALLOWED_UPLOAD_CONTENT_TYPES", [])
        if allowed_types and value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"File type '{value.content_type}' is not allowed. Accepted types: {', '.join(allowed_types)}."
            )
        return value

    def update(self, instance, validated_data):
        profile_pic_key = validated_data.pop("profile_pic_key", None)
        if profile_pic_key:
            validated_data["profile_pic"] = profile_pic_key
        return super().update(instance, validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        fields = ["phone_number"]


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "zipcode", "password")

    def create(self, validated_data):
        # Create user as inactive — must verify OTP to become active
        user = User.objects.create_user(
            phone_number=validated_data.get("phone_number"),
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            zipcode=validated_data.get("zipcode", ""),
            is_active=False,
        )
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)

    class Meta:
        fields = ["phone_number", "otp_code"]


class VerifySignupOTPSerializer(serializers.Serializer):
    """Verifies the signup OTP and activates the user account."""

    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)

    class Meta:
        fields = ["phone_number", "otp_code"]


class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    type = serializers.ChoiceField(choices=["signup", "forgot_password"])

    class Meta:
        fields = ["phone_number", "type"]


class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        fields = ["phone_number", "otp_code", "password"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        fields = ["old_password", "new_password"]

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
