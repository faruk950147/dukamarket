from django.urls import path
from account.api_views import *

urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("verify-otp/", OTPVerifyView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),

    path("profile/", ProfileView.as_view()),
    path("change-password/", PasswordChangeView.as_view()),

    path("reset-password/", PasswordResetRequestView.as_view()),
    path("reset-password-verify/", PasswordResetVerifyView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),
]