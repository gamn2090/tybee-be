
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
        if hasattr(default_storage, 'bucket'):
            region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=region,
                endpoint_url=f'https://s3.{region}.amazonaws.com'
            )
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            key = value.name
            try:
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': key},
                    ExpiresIn=3600
                )
                return presigned_url
            except Exception:
                return url
        return url



class UserSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(write_only=True, required=False, allow_null=True)
    profile_pic_presigned = PresignedUrlField(source='profile_pic', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'phone_number', 'zipcode', 'is_active', 'date_joined', 'profile_pic', 'profile_pic_presigned')


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    class Meta:
        fields = ['phone_number']

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    otp_code = serializers.CharField(write_only=True)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'zipcode', 'password', 'otp_code', 'access_token', 'refresh_token')
    
    def validate_otp_code(self, value):
        if not value:
            raise serializers.ValidationError("OTP code is required.")
        
        otp = signupOTP.objects.filter(otp_code=value, is_used=False).exists()
        if not otp:
            raise serializers.ValidationError("Invalid OTP code.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data.get('phone_number'),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            zipcode=validated_data.get('zipcode', '')
        )
        otp = signupOTP.objects.filter(user=user, otp_code=validated_data['otp_code'], is_used=False).exists()
        if otp:
            otp.is_used = True
            otp.save()
        else:
            raise serializers.ValidationError("Invalid OTP code.")
        refresh = RefreshToken.for_user(user)
        user._refresh_token = str(refresh)
        user._access_token = str(refresh.access_token)
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Add tokens to response if present
        ret['refresh_token'] = getattr(instance, '_refresh_token', None)
        ret['access_token'] = getattr(instance, '_access_token', None)
        return ret

class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)

    class Meta:
        fields = ['phone_number', 'otp_code']

class ForgotPasswordConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        fields = ['phone_number', 'otp_code', 'password']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, min_length=8)
    new_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        fields = ['old_password', 'new_password']

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
