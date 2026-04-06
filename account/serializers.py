from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

from account.models import OTP
from account.tasks import send_otp_email_api

User = get_user_model()


# =========================
# Signup Serializer
# =========================
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password", "password2"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"detail": "Passwords do not match"})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()

        # Delete old OTP
        OTP.objects.filter(user=user, otp_type="register").delete()

        # Create new OTP
        otp_obj, otp = OTP.create_otp(user, "register")

        # Send OTP
        send_otp_email_api.delay(user.email, otp)

        return user


# =========================
# OTP Verify Serializer
# =========================
class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    otp = serializers.CharField(write_only=True, max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value

    def validate(self, attrs):
        email = attrs.get("email")
        otp_code = attrs.get("otp")

        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"detail": "User not found"})

        otp_obj = OTP.objects.filter(user=user, otp_type="register").order_by("-created_at").first()
        if not otp_obj:
            raise serializers.ValidationError({"detail": "OTP not found"})

        # Use dict keys from verify_otp
        result = otp_obj.verify_otp(otp_code)
        if not result.get("success"):
            raise serializers.ValidationError({"detail": f"OTP failed: {result.get('message', 'Unknown error')}"})

        # Activate user
        user.is_active = True
        user.save(update_fields=["is_active"])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            "user_id": user.id,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


# =========================
# Login Serializer
# =========================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    keep_logged_in = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            user_obj = User.objects.filter(email=username).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)

        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials"})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Account not verified"})

        refresh = RefreshToken.for_user(user)
        if attrs.get("keep_logged_in"):
            refresh.set_exp(lifetime=timedelta(days=30))
        else:
            refresh.set_exp(lifetime=timedelta(days=1))

        return {
            "user_id": user.id,
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


# =========================
# Logout Serializer
# =========================
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs.get("refresh")
        return attrs

    def save(self):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise ValidationError({"detail": "Invalid or expired token"})


# =========================
# Password Change Serializer
# =========================
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"detail": "Passwords do not match"})

        validate_password(attrs["new_password"])

        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"detail": "Wrong old password"})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


# =========================
# Password Reset Request Serializer
# =========================
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            OTP.objects.filter(user=user, otp_type="reset").delete()
            otp_obj, otp = OTP.create_otp(user, "reset")
            send_otp_email_api.delay(user.email, otp)
        return attrs


# =========================
# Password Reset Verify Serializer
# =========================
class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    otp = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs.get("email")).first()
        if not user:
            raise serializers.ValidationError({"detail": "Invalid email"})

        otp_obj = OTP.objects.filter(user=user, otp_type="reset", is_used=False).order_by("-created_at").first()
        if not otp_obj:
            raise serializers.ValidationError({"detail": "OTP not found"})

        result = otp_obj.verify_otp(attrs.get("otp"))
        if not result.get("success"):
            raise serializers.ValidationError({"detail": f"OTP failed: {result.get('message', 'Unknown error')}"})

        validate_password(attrs.get("new_password"))
        attrs["user"] = user
        attrs["otp_obj"] = otp_obj
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp_obj = self.validated_data["otp_obj"]

        user.set_password(self.validated_data["new_password"])
        user.save()

        otp_obj.is_used = True
        otp_obj.save()
        return user


# =========================
# Profile Serializer
# =========================
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "phone", "image",
            "country", "city", "home_city",
            "zip_code", "address",
            "created_at", "updated_at"
        ]
        read_only_fields = ["email"]

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


# =========================
# Resend OTP Serializer
# =========================
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"detail": "User not found"})
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]

        last_otp = OTP.objects.filter(user=user, otp_type="register").order_by("-created_at").first()
        if last_otp:
            diff = (timezone.now() - last_otp.created_at).total_seconds()
            if diff < OTP.RESEND_INTERVAL_SECONDS:
                remaining = OTP.RESEND_INTERVAL_SECONDS - diff
                raise serializers.ValidationError({"detail": f"Wait {int(remaining)} seconds before requesting new OTP"})

        OTP.objects.filter(user=user, otp_type="register", is_used=False).update(is_used=True)

        otp_obj, otp = OTP.create_otp(user, "register")
        send_otp_email_api.delay(user.email, otp)

        return otp_obj