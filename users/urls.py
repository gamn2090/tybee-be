from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignupView, UserViewSet, LoginView, ForgotPasswordView, ResetPasswordView, SendSignupOTPView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('send-signup-otp/', SendSignupOTPView.as_view(), name='send-signup-otp'),
    path('', include(router.urls)),
]
