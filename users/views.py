from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from .models import User, PasswordResetOTP, signupOTP
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    UserSerializer,
    SignupSerializer,
    ForgotPasswordConfirmSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    VerifySignupOTPSerializer,
)
from django.utils import timezone
from django.core.mail import send_mail
import random
import string
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .utils import send_sms_otp


@extend_schema(tags=["Password & OTP"])
class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # If the account is not yet verified, signal the frontend to redirect
        # to the OTP verification flow rather than the password-reset flow.
        if not user.is_active:
            return Response(
                {
                    "detail": "No active account found with the given credentials",
                    "requires_otp_verification": True,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Generate random OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        PasswordResetOTP.objects.create(
            user=user, otp_code=otp_code, expires_at=expires_at
        )

        # Send OTP via Twilio
        custom_message = f"Your Tybee password reset code is: {otp_code}"
        send_sms_otp(phone_number, otp_code, custom_message)

        print(f"[DEBUG] OTP for {phone_number}: {otp_code}")
        return Response({"detail": "OTP sent to phone number.", "OTP": otp_code})


@extend_schema(tags=["Password & OTP"])
class VerifyOTPView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        otp_code = serializer.validated_data.get("otp_code")
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
        try:
            otp = PasswordResetOTP.objects.filter(
                user=user, otp_code=otp_code, is_used=False
            ).latest("expires_at")
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST
            )
        if otp.expires_at < timezone.now():
            return Response(
                {"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            otp.is_used = True
            otp.save()
        return Response({"detail": "OTP verified successfully."})


@extend_schema(tags=["Password & OTP"])
class ForgetPasswordConfirmView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        new_password = serializer.validated_data.get("password")
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password reset successful."})


@extend_schema(tags=["Password & OTP"])
class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        new_password = serializer.validated_data.get("new_password")
        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully."})


@extend_schema(tags=["Signup & Login"])
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # If SimpleJWT returned a 401, check whether the account exists but
        # is inactive (unverified). If so, add the flag so the frontend can
        # redirect the user to the OTP verification screen instead of showing
        # a generic "wrong credentials" message.
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            phone_number = request.data.get("phone_number") or request.data.get("username")
            if phone_number:
                try:
                    user = User.objects.get(phone_number=phone_number)
                    if not user.is_active:
                        response.data["requires_otp_verification"] = True
                except User.DoesNotExist:
                    pass  # Wrong credentials — leave response untouched

        return response


@extend_schema(tags=["Signup & Login"])
class SendOTPView(generics.GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        
        user_qs = User.objects.filter(phone_number=phone_number)
        if user_qs.exists():
            user = user_qs.first()
            if not user.is_active:
                # User exists but is inactive. Resend OTP and return flag
                otp_code = "".join(random.choices(string.digits, k=6))
                expires_at = timezone.now() + timezone.timedelta(minutes=10)
                
                # Invalidate previous OTPs
                signupOTP.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)
                
                signupOTP.objects.create(
                    phone_number=phone_number, otp_code=otp_code, expires_at=expires_at
                )

                custom_message = f"Your Tybee signup verification code is: {otp_code}"
                send_sms_otp(phone_number, otp_code, custom_message)

                print(f"[DEBUG] OTP for {phone_number}: {otp_code} (Inactive User)")

                return Response({
                    "detail": "Account exists but not verified. OTP resent.", 
                    "OTP": otp_code,
                    "requires_otp_verification": True
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"detail": "User with phone number already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Generate random OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        signupOTP.objects.create(
            phone_number=phone_number, otp_code=otp_code, expires_at=expires_at
        )

        # Send OTP via Twilio
        custom_message = f"Your Tybee signup verification code is: {otp_code}"
        send_sms_otp(phone_number, otp_code, custom_message)

        print(f"[DEBUG] OTP for {phone_number}: {otp_code}")

        return Response({"detail": "OTP sent to phone number.", "OTP": otp_code})


@extend_schema(tags=["Signup & Login"])
class ResendOTPView(generics.GenericAPIView):
    """
    Resend OTP for both signup and forgot password flows.
    - type = 'signup'          → returns prefixed OTP 654321 (phone must NOT be registered)
    - type = 'forgot_password' → returns prefixed OTP 654321 (phone must be registered)
    All previous OTPs for the phone are invalidated before issuing the new one.
    """

    serializer_class = ResendOTPSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        otp_type = serializer.validated_data.get("type")

        # Resend OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        if otp_type == "signup":
            if User.objects.filter(phone_number=phone_number, is_active=True).exists():
                return Response(
                    {"detail": "User with this phone number already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Invalidate all previous signup OTPs for this phone
            signupOTP.objects.filter(phone_number=phone_number, is_used=False).update(
                is_used=True
            )
            signupOTP.objects.create(
                phone_number=phone_number, otp_code=otp_code, expires_at=expires_at
            )

        elif otp_type == "forgot_password":
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND
                )
            # Invalidate all previous forgot-password OTPs for this user
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(
                is_used=True
            )
            PasswordResetOTP.objects.create(
                user=user, otp_code=otp_code, expires_at=expires_at
            )

        # Send OTP via Twilio
        flow_name = "signup" if otp_type == "signup" else "password reset"
        custom_message = f"Your requested Tybee {flow_name} code is: {otp_code}"
        send_sms_otp(phone_number, otp_code, custom_message)

        print(f"[DEBUG] Resend OTP ({otp_type}) for {phone_number}: {otp_code}")
        return Response({"detail": "OTP resent to phone number.", "OTP": otp_code})


@extend_schema(tags=["Signup & Login"])
class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number")
        if phone_number:
            try:
                user = User.objects.get(phone_number=phone_number)
                if not user.is_active:
                    # User exists but is inactive. Update details, resend OTP
                    user.first_name = request.data.get("first_name", user.first_name)
                    user.last_name = request.data.get("last_name", user.last_name)
                    user.zipcode = request.data.get("zipcode", user.zipcode)
                    if request.data.get("password"):
                        user.set_password(request.data.get("password"))
                    user.save()

                    # Invalidate old OTPs
                    signupOTP.objects.filter(phone_number=phone_number, is_used=False).update(is_used=True)

                    # Generate and send new OTP
                    otp_code = "".join(random.choices(string.digits, k=6))
                    expires_at = timezone.now() + timezone.timedelta(minutes=10)
                    signupOTP.objects.create(
                        phone_number=phone_number, otp_code=otp_code, expires_at=expires_at
                    )

                    custom_message = f"Your Tybee signup verification code is: {otp_code}"
                    send_sms_otp(phone_number, otp_code, custom_message)

                    print(f"[DEBUG] Signup OTP for {phone_number} (Inactive User Restored): {otp_code}")

                    return Response({
                        "detail": "Account exists but not verified. Details updated and OTP resent.",
                        "OTP": otp_code,
                        "requires_otp_verification": True
                    }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                pass # Proceed normally

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")

        # Create the user as inactive
        user = serializer.save()

        # Generate random and store OTP for this phone number
        otp_code = "".join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        signupOTP.objects.create(
            phone_number=phone_number, otp_code=otp_code, expires_at=expires_at
        )

        # Send OTP via Twilio
        custom_message = f"Your Tybee signup verification code is: {otp_code}"
        send_sms_otp(phone_number, otp_code, custom_message)

        print(f"[DEBUG] Signup OTP for {phone_number}: {otp_code}")

        return Response(
            {
                "detail": "Account created. Please verify the OTP to activate your account.",
                "OTP": otp_code,
                "requires_otp_verification": True
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Signup & Login"])
class VerifySignupOTPView(generics.GenericAPIView):
    """
    Verify the OTP sent at signup.
    On success: activates the user account and returns JWT tokens.
    """

    serializer_class = VerifySignupOTPSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data.get("phone_number")
        otp_code = serializer.validated_data.get("otp_code")

        # Find the user (still inactive)
        try:
            user = User.objects.get(phone_number=phone_number, is_active=False)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found or already active."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Find a valid, unused OTP for this phone
        try:
            otp = signupOTP.objects.filter(
                phone_number=phone_number, otp_code=otp_code, is_used=False
            ).latest("expires_at")
        except signupOTP.DoesNotExist:
            return Response(
                {"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST
            )

        if otp.expires_at < timezone.now():
            return Response(
                {"detail": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Mark OTP as used and activate the user
        otp.is_used = True
        otp.save()
        user.is_active = True
        user.save()

        # Return JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": "Account verified successfully.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
        )


@extend_schema(tags=["Profile"])
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "put"]
