from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.sites import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.conf import settings
import logging

# Import from local
from account.mixing import LoginRequiredMixin, LogoutRequiredMixin
from account.forms import *

logger = logging.getLogger('project')

# =========================
# Signup View
# =========================
@method_decorator(never_cache, name='dispatch')
class SignupView(LogoutRequiredMixin, View):
    def get(self, request):
        return render(request, 'account/signup.html')

    def post(self, request):

        return render(request, 'account/signup.html')


# =========================
# OTP Verify View
# =========================
@method_decorator(never_cache, name='dispatch')
class OTPVerifyView(LogoutRequiredMixin, View):
    def get(self, request):
        return render(request, 'account/otp_verify.html')

    def post(self, request):

        return render(request, 'account/otp_verify.html')


# =========================
# Login View
# =========================
@method_decorator(never_cache, name='dispatch')
class LoginView(LogoutRequiredMixin, View):
    def get(self, request):
        return render(request, 'account/login.html')

    def post(self, request):

        return render(request, 'account/login.html')


# =========================
# Logout View
# =========================
@method_decorator([never_cache, login_required], name='dispatch')
class LogoutView(View):
    def get(self, request):
        username = request.user.username
        try:
            logout(request)
            messages.success(request, f"{username} has been logged out successfully.")
            logger.info(f"User logged out: {username}")
        except Exception as e:
            logger.error(f"Logout error: {e}")
            messages.error(request, f"Logout error: {e}")
        return redirect('login')


# =========================
# Resend OTP View
# =========================
class ResendOTPView(View):
    def get(self, request, *args, **kwargs):
        pass
    
    def post(self, request, *args, **kwargs):
        pass

