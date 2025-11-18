from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from .models import User, PasswordResetOTP
from .serializers import UserSerializer, SignupSerializer, PasswordResetOTPSerializer
from django.utils import timezone
from django.core.mail import send_mail
import random
import string


# Send OTP for signup (no user yet)
class SendSignupOTPView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	def post(self, request):
		email = request.data.get('email')
		if not email:
			return Response({'detail': 'Email required.'}, status=status.HTTP_400_BAD_REQUEST)
		# Generate OTP
		otp_code = ''.join(random.choices(string.digits, k=6))
		expires_at = timezone.now() + timezone.timedelta(minutes=10)
		PasswordResetOTP.objects.create(user=None, email=email, otp_code=otp_code, expires_at=expires_at)
		send_mail(
			'Your Signup OTP',
			f'Your OTP code is: {otp_code}',
			None,
			[email],
		)
		return Response({'detail': 'Signup OTP sent to email.'})

class ForgotPasswordView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	def post(self, request):
		email = request.data.get('email')
		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
		# Generate OTP
		otp_code = ''.join(random.choices(string.digits, k=6))
		expires_at = timezone.now() + timezone.timedelta(minutes=10)
		PasswordResetOTP.objects.create(user=user, otp_code=otp_code, expires_at=expires_at)
		# Send OTP via email (simple example)
		send_mail(
			'Your Password Reset OTP',
			f'Your OTP code is: {otp_code}',
			None,
			[user.email],
		)
		return Response({'detail': 'OTP sent to email.'})

class ResetPasswordView(generics.GenericAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = PasswordResetOTPSerializer

	def post(self, request):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data.get('email')
		otp_code = serializer.validated_data.get('otp_code')
		new_password = serializer.validated_data.get('password')
		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
		try:
			otp = PasswordResetOTP.objects.filter(user=user, otp_code=otp_code, is_used=False).latest('expires_at')
		except PasswordResetOTP.DoesNotExist:
			return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
		if otp.expires_at < timezone.now():
			return Response({'detail': 'OTP expired.'}, status=status.HTTP_400_BAD_REQUEST)
		user.set_password(new_password)
		user.save()
		otp.is_used = True
		otp.save()
		return Response({'detail': 'Password reset successful.'})

class LoginView(TokenObtainPairView):
	permission_classes = [permissions.AllowAny]

class SignupView(generics.CreateAPIView):
	serializer_class = SignupSerializer
	permission_classes = [permissions.AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		email = serializer.validated_data.get('email')
		otp_code = serializer.validated_data.get('otp')
		# Check OTP
		try:
			otp = PasswordResetOTP.objects.filter(user__email=email, otp_code=otp_code, is_used=False).latest('expires_at')
		except PasswordResetOTP.DoesNotExist:
			return Response({'detail': 'Invalid or missing OTP.'}, status=status.HTTP_400_BAD_REQUEST)
		if otp.expires_at < timezone.now():
			return Response({'detail': 'OTP expired.'}, status=status.HTTP_400_BAD_REQUEST)
		# Mark OTP as used
		otp.is_used = True
		otp.save()
		return super().create(request, *args, **kwargs)

class UserViewSet(viewsets.ModelViewSet):
	queryset = User.objects.all()
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAdminUser]
	http_method_names = ['get', 'post', 'delete', "put"]

