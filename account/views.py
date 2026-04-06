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
from account.forms import SignupForm, OTPVerifyForm, LoginForm

logger = logging.getLogger('project')

# =========================
# Signup View
# =========================
@method_decorator(never_cache, name='dispatch')
class SignupView(LogoutRequiredMixin, View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'account/signup.html', {'form': form})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created. Please verify OTP sent to your email.")
            return redirect('otp_verify')
        return render(request, 'account/signup.html', {'form': form})


# =========================
# OTP Verify View
# =========================
@method_decorator(never_cache, name='dispatch')
class OTPVerifyView(LogoutRequiredMixin, View):
    def get(self, request):
        form = OTPVerifyForm()
        return render(request, 'account/otp_verify.html', {'form': form})

    def post(self, request):
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)  # Login user after OTP verified
            messages.success(request, "OTP verified successfully. You are now logged in.")
            logger.info(f"User verified and logged in: {user.username} ({user.id})")
            return redirect(settings.LOGIN_REDIRECT_URL)  # e.g., dashboard
        return render(request, 'account/otp_verify.html', {'form': form})


# =========================
# Login View
# =========================
@method_decorator(never_cache, name='dispatch')
class LoginView(LogoutRequiredMixin, View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'account/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            logger.info(f"User logged in: {user.username} ({user.id})")
            return redirect(settings.LOGIN_REDIRECT_URL)
        return render(request, 'account/login.html', {'form': form})


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
        form = ResendOTPForm()
        return render(request, "resend_otp.html", {"form": form})
    
    def post(self, request, *args, **kwargs):
        form = ResendOTPForm(request.POST)
        if form.is_valid():
            # OTP already sent inside form's clean_email
            return JsonResponse({
                "status": "success",
                "message": "New OTP has been sent to your email."
            })
        else:
            # Return first validation error
            error_msg = next(iter(form.errors.values()))[0]
            return JsonResponse({
                "status": "error",
                "message": error_msg
            })

