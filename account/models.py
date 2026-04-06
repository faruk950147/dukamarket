from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.utils.html import mark_safe
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import hashlib, hmac, secrets

# =========================
# Validators
# =========================
phone_validator = RegexValidator(r"^\+?\d{10,15}$", "Enter a valid phone number")


# =========================
# User Manager
# =========================
class Manager(BaseUserManager):

    def normalize_phone(self, phone):
        phone = phone.replace(" ", "").strip()
        if phone.startswith("+880"):
            return phone
        if phone.startswith("880"):
            return "+" + phone
        if phone.startswith("01"):
            return "+880" + phone[1:]
        return phone

    def create_user(self, username, email, phone, password=None, **extra_fields):
        if not username:
            raise ValueError("Username required")
        if not email:
            raise ValueError("Email required")
        if not phone:
            raise ValueError("Phone required")

        email = self.normalize_email(email)
        phone = self.normalize_phone(phone)

        user = self.model(
            username=username,
            email=email,
            phone=phone,
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(username, email, phone, password, **extra_fields)


# =========================
# User Model
# =========================
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator()])
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=15, unique=True, validators=[phone_validator], db_index=True)

    image = models.ImageField(upload_to="users/", blank=True, null=True)

    country = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    city = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    home_city = models.CharField(max_length=150, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = Manager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone"]

    class Meta:
        verbose_name = "01. User"
        verbose_name_plural = "01. Users"
        db_table = "user"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["country", "city"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.username or str(self.id)

    @property
    def image_tag(self):
        if self.image and hasattr(self.image, "url"):
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return mark_safe("<span>No Image</span>")


# =========================
# OTP Model
# =========================
class OTP(models.Model):
    OTP_LENGTH = getattr(settings, "OTP_LENGTH", 6)
    OTP_EXPIRY_MINUTES = getattr(settings, "OTP_EXPIRY_MINUTES", 5)
    RESEND_INTERVAL_SECONDS = getattr(settings, "OTP_RESEND_INTERVAL", 60)
    MAX_USE_COUNT = getattr(settings, "OTP_MAX_USE_COUNT", 5)

    OTP_TYPE_CHOICES = (
        ("register", "Register"),
        ("reset", "Password Reset"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES)

    otp_hash = models.CharField(max_length=64)
    otp_salt = models.CharField(max_length=16)

    is_used = models.BooleanField(default=False)
    used_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "02. OTP"
        verbose_name_plural = "02. OTPs"
        db_table = "otp"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "otp_type", "created_at"]),
            models.Index(fields=["user", "otp_type", "is_used"]),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.otp_type}"

    # =========================
    # Status Check
    # =========================
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

    def is_valid(self):
        return not self.is_used and self.used_count < self.MAX_USE_COUNT and not self.is_expired()

    # =========================
    # Standard Response
    # =========================
    @staticmethod
    def response(success, code, message):
        return {"success": success, "code": code, "message": message}

    # =========================
    # Verify OTP (Race-safe)
    # =========================
    def verify_otp(self, otp):
        if not otp.isdigit() or len(otp) != self.OTP_LENGTH:
            return self.response(False, "invalid", "Invalid OTP")

        with transaction.atomic():
            otp_obj = OTP.objects.select_for_update().filter(id=self.id).first()
            if not otp_obj:
                return self.response(False, "invalid", "OTP not found")

            if otp_obj.used_count >= self.MAX_USE_COUNT:
                return self.response(False, "blocked", "Too many attempts")

            if not otp_obj.is_valid():
                return self.response(False, "expired", "OTP expired")

            hashed = OTP.hash_otp(otp, otp_obj.otp_salt)

            if otp_obj.used_count > 0:
                # Non-blocking alternative: consider async or frontend delay
                pass

            if hmac.compare_digest(hashed, otp_obj.otp_hash):
                otp_obj.is_used = True
                otp_obj.save(update_fields=["is_used"])

                if otp_obj.otp_type == "register" and not otp_obj.user.is_verified:
                    otp_obj.user.is_verified = True
                    otp_obj.user.save(update_fields=["is_verified"])

                return self.response(True, "success", "OTP verified")

            otp_obj.used_count += 1
            otp_obj.save(update_fields=["used_count"])

        return self.response(False, "invalid", "Wrong OTP")

    # =========================
    # Hash OTP
    # =========================
    @staticmethod
    def hash_otp(otp, salt):
        secret = getattr(settings, "OTP_SECRET_KEY", "default_secret")
        return hashlib.sha256(f"{otp}{salt}{secret}".encode()).hexdigest()

    # =========================
    # Generate OTP
    # =========================
    @classmethod
    def generate_otp(cls):
        return ''.join(secrets.choice("0123456789") for _ in range(cls.OTP_LENGTH))

    # =========================
    # Create OTP
    # =========================
    @classmethod
    def create_otp(cls, user, otp_type, otp=None):
        with transaction.atomic():
            qs = cls.objects.select_for_update().filter(
                user=user,
                otp_type=otp_type
            ).order_by("-created_at")

            last_otp = qs.first() if qs else None
            if last_otp:
                diff = int((timezone.now() - last_otp.created_at).total_seconds())
                if diff < cls.RESEND_INTERVAL_SECONDS:
                    remaining = cls.RESEND_INTERVAL_SECONDS - diff
                    raise ValueError(f"Wait {remaining} seconds before requesting new OTP")

            cls.objects.filter(
                user=user,
                otp_type=otp_type,
                is_used=False
            ).update(is_used=True)

            if otp is None:
                otp = cls.generate_otp()

            salt = secrets.token_hex(8)

            otp_instance = cls.objects.create(
                user=user,
                otp_type=otp_type,
                otp_salt=salt,
                otp_hash=cls.hash_otp(otp, salt)
            )

            return otp_instance, otp