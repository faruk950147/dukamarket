from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from account.tasks import send_otp_email_web
from rest_framework_simplejwt.tokens import RefreshToken
import random
from datetime import timedelta

User = get_user_model()


# =========================
# Signup Form (Production Ready)
# =========================
