from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from .models import User, PasswordResetOTP
from .serializers import ChangePasswordSerializer, ForgotPasswordSerializer, UserSerializer, SignupSerializer, ForgotPasswordConfirmSerializer, VerifyOTPSerializer
from django.utils import timezone
from django.core.mail import send_mail
import random
import string
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.parsers import MultiPartParser, FormParser


@extend_schema(tags=["Password & OTP"])
class ForgotPasswordView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = ForgotPasswordSerializer
	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		phone_number = serializer.validated_data.get('phone_number')
		try:
			user = User.objects.get(phone_number=phone_number)
		except User.DoesNotExist:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
		# Generate OTP
		otp_code = ''.join(random.choices(string.digits, k=6))
		expires_at = timezone.now() + timezone.timedelta(minutes=10)
		PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)
		# Placeholder for phone OTP integration
		# TODO: Integrate with actual phone OTP service (e.g., Twilio, MSG91, etc.)
		print(f"[DEBUG] OTP for {phone_number}: {otp_code}")
		return Response({'detail': 'OTP sent to phone number.', "OTP": otp_code})


@extend_schema(tags=["Password & OTP"])
class VerifyOTPView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = VerifyOTPSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		phone_number = serializer.validated_data.get('phone_number')
		otp_code = serializer.validated_data.get('otp_code')
		try:
			user = User.objects.get(phone_number=phone_number)
		except User.DoesNotExist:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
		try:
			otp = PasswordResetOTP.objects.filter(user=user, otp_code=otp_code, is_used=False).latest('expires_at')
		except PasswordResetOTP.DoesNotExist:
			return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
		if otp.expires_at < timezone.now():
			return Response({'detail': 'OTP expired.'}, status=status.HTTP_400_BAD_REQUEST)
		else:
			otp.is_used = True
			otp.save()
		return Response({'detail': 'OTP verified successfully.'})


@extend_schema(tags=["Password & OTP"])
class ForgetPasswordConfirmView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = ForgotPasswordConfirmSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		phone_number = serializer.validated_data.get('phone_number')
		new_password = serializer.validated_data.get('password')
		try:
			user = User.objects.get(phone_number=phone_number)
		except User.DoesNotExist:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
		user.set_password(new_password)
		user.save()
		return Response({'detail': 'Password reset successful.'})


@extend_schema(tags=["Password & OTP"])
class ChangePasswordView(generics.GenericAPIView):
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = ChangePasswordSerializer
	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = request.user
		new_password = serializer.validated_data.get('new_password')
		user.set_password(new_password)
		user.save()
		return Response({'detail': 'Password changed successfully.'})

@extend_schema(tags=["Signup & Login"])
class LoginView(TokenObtainPairView):
	permission_classes = [permissions.AllowAny]

@extend_schema(tags=["Signup & Login"])
class SendOTPView(generics.GenericAPIView):
	serializer_class = ForgotPasswordSerializer
	permission_classes = [permissions.AllowAny]

	def post(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		phone_number = serializer.validated_data.get('phone_number')
		user = User.objects.filter(phone_number=phone_number)
		if user.exists():
			return Response({'detail': 'User with phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)
		# Generate OTP
		otp_code = ''.join(random.choices(string.digits, k=6))
		expires_at = timezone.now() + timezone.timedelta(minutes=10)
		SignupOTP.objects.create(otp_code=otp_code, expires_at=expires_at)
		#TODO: Integrate with actual phone OTP service (e.g., Twilio, MSG91, etc.)
		print(f"[DEBUG] OTP for {phone_number}: {otp_code}")
		
		return Response({'detail': 'OTP sent to phone number.', "OTP": otp_code})

@extend_schema(tags=["Signup & Login"])
class SignupView(generics.CreateAPIView):
	serializer_class = SignupSerializer
	permission_classes = [permissions.AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return super().create(request, *args, **kwargs)

@extend_schema(tags=["Profile"])
class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	parser_classes = (MultiPartParser, FormParser)
	permission_classes = [permissions.IsAdminUser]
	http_method_names = ['get', 'post', 'delete', "put"]
