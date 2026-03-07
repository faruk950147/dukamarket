from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.utils.html import mark_safe

# Phone Validator
phone_validator = RegexValidator(
    r"^(\+?\d{0,4})?\s?-?\s?(\(?\d{3}\)?)\s?-?\s?(\(?\d{3}\)?)\s?-?\s?(\(?\d{4}\)?)?$",
    "The phone number provided is invalid"
)

# User Manager
class Manager(BaseUserManager):
    def create_user(self, username, password=None, email=None, phone=None, **extra_fields):
        if not username:
            raise ValueError("Username must be set")
        if not email and not phone:
            raise ValueError("Email or Phone must be set")

        if email:
            email = self.normalize_email(email)

        user = self.model(username=username, email=email, phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # social login etc.

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email=None, phone=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not email and not phone:
            email = "admin@gmail.com"

        return self.create_user(username, password, email, phone, **extra_fields)


# Custom User Model
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator()]
    )
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, validators=[phone_validator], unique=True, blank=True, null=True)
    
    image = models.ImageField(upload_to='user/', default='defaults/default.jpg')
    country = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    city = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    home_city = models.CharField(max_length=150, blank=True, null=True)
    zip_code = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(max_length=500, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = Manager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []  # optional email/phone

    class Meta:
        ordering = ['id']
        verbose_name_plural = '01. Users'
        indexes = [
            models.Index(fields=['country', 'city']),
        ]

    @property
    def image_tag(self):
        # getattr() returns the value of an attribute.
        # If the attribute does not exist, it returns the default value (if provided).
        img = getattr(self, 'image', None)
        # hasattr() checks if an object has a specific attribute.
        # It returns True if the attribute exists, otherwise False.
        if img and hasattr(img, 'url'):
            return mark_safe(
                f'<img src="{img.url}" style="max-width:50px; max-height:50px;" />'
            )
        return mark_safe('<span>No Image</span>')

    def __str__(self):
        return self.username