from rest_framework import serializers
from .models import User, PasswordResetOTP

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number','zipcode', 'is_active', 'date_joined', 'social_provider')

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    otp = serializers.CharField(write_only=True, max_length=6)
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'zipcode', 'password', 'otp')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            zipcode=validated_data.get('zipcode', '')
        )
        return user

class PasswordResetOTPSerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        fields = ['email', 'otp_code', 'password']
