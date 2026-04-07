from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

from account.tasks import send_otp_email_api

User = get_user_model()


