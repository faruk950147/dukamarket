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
class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}))

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("password2"):
            raise forms.ValidationError("Passwords do not match")
        # Rate-limiting / brute force prevention hooks can be added here
        return cleaned_data

    def save(self, commit=True):
        # form preparing process but not saving to database
        user = super().save(commit=False)
        # setting password securely using Django's set_password method
        user.set_password(self.cleaned_data["password"])
        # user can login after OTP verification
        user.is_active = False
        if commit:
            user.save()
            # Remove old OTPs because we are creating new one so old one is not needed
            otp = random.randint(100000, 999999)
            send_otp_email_web.delay(user.email, otp)
        return user


# =========================
# OTP Verification Form
# =========================
class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))
    otp = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "OTP"}))

    def clean_otp(self):
        otp = self.cleaned_data.get("otp")
        if not otp.isdigit():
            raise forms.ValidationError("OTP must be numeric")
        return otp

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        otp_code = cleaned_data.get("otp")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("User not found")

        otp_instance = OTP.objects.filter(user=user, otp_type="register").order_by("-created_at").first()
        if not otp_instance or otp_instance.is_expired() or otp_instance.is_used:
            raise forms.ValidationError("OTP expired or invalid")

        status = otp_instance.verify_otp(otp_code)
        if status != "success":
            raise forms.ValidationError(f"OTP verification failed: {status}")

        # Activate user
        user.is_active = True
        user.save(update_fields=["is_active"])

        # JWT token generation
        refresh = RefreshToken.for_user(user)
        cleaned_data["user"] = user
        cleaned_data["access"] = str(refresh.access_token)
        cleaned_data["refresh"] = str(refresh)
        return cleaned_data


# =========================
# Login Form
# =========================
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))
    keep_logged_in = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        keep_logged_in = cleaned_data.get("keep_logged_in")

        user = authenticate(username=username, password=password)

        if not user:
            raise forms.ValidationError("Invalid credentials")

        if not user.is_active:
            raise forms.ValidationError("Account is disabled")

        if not getattr(user, "is_verified", True):
            raise forms.ValidationError("Account not verified")

        # JWT Token Generate
        refresh = RefreshToken.for_user(user)

        # Keep logged in logic (JWT lifetime)
        if keep_logged_in:
            refresh.set_exp(lifetime=timedelta(days=30))  # 30 days
        else:
            refresh.set_exp(lifetime=timedelta(days=1))   # 1 day

        # Save data
        cleaned_data["user"] = user
        cleaned_data["access"] = str(refresh.access_token)
        cleaned_data["refresh"] = str(refresh)

        return cleaned_data


# =========================
# Password Change Form
# =========================
class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Old Password"}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "New Password"}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        if not self.user.check_password(cleaned_data.get("old_password")):
            raise forms.ValidationError("Wrong old password")
        validate_password(cleaned_data.get("new_password"))
        return cleaned_data


# =========================
# Password Reset Request Form
# =========================
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))

    def clean_email(self):
        email = self.cleaned_data.get("email")
        try:
            user = User.objects.get(email=email)
            otp_instance, otp = OTP.create_otp(user=user, otp_type="reset")
            send_otp_email_web.delay(user.email, otp)
        except User.DoesNotExist:
            pass  # Security: don't reveal if email exists
        return email


# =========================
# Password Reset Verify Form
# =========================
class PasswordResetVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "OTP"}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "New Password"}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        otp_code = cleaned_data.get("otp")
        new_password = cleaned_data.get("new_password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid email")

        otp_obj = OTP.objects.filter(user=user, otp_type="reset", is_used=False).order_by("-created_at").first()
        if not otp_obj or otp_obj.is_expired() or otp_obj.verify_otp(otp_code) != "success":
            raise forms.ValidationError("Invalid or expired OTP")

        validate_password(new_password)
        cleaned_data["user"] = user
        return cleaned_data


# =========================
# Profile Form
# =========================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'phone', 'image', 'country', 'city', 'home_city', 'zip_code', 'address']
        widgets = {
            'username': forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
            'phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
            'image': forms.FileInput(attrs={"class": "form-control"}),
            'country': forms.TextInput(attrs={"class": "form-control", "placeholder": "Country"}),
            'city': forms.TextInput(attrs={"class": "form-control", "placeholder": "City"}),
            'home_city': forms.TextInput(attrs={"class": "form-control", "placeholder": "Home City"}),
            'zip_code': forms.TextInput(attrs={"class": "form-control", "placeholder": "Zip Code"}),
            'address': forms.Textarea(attrs={"class": "form-control", "placeholder": "Address"}),
        }
  
        
class ResendOTPForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "class": "form-control",
        "placeholder": "Email"
    }))

    def clean_email(self):
        email = self.cleaned_data.get("email")

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Invalid email")

        # Check last OTP for resend interval
        last_otp_qs = OTP.objects.filter(user=user, otp_type="register", is_used=False).order_by("-created_at")
        if last_otp_qs.exists():
            last_otp = last_otp_qs[0]  # Avoid using .first()
            diff = (timezone.now() - last_otp.created_at).total_seconds()
            if diff < OTP.RESEND_INTERVAL_SECONDS:
                remaining = int(OTP.RESEND_INTERVAL_SECONDS - diff)
                raise ValidationError(f"Wait {remaining} seconds before requesting a new OTP")

        # Deactivate old unused OTPs
        last_otp_qs.update(is_used=True)

        # Generate new OTP (move logic here instead of inside form clean for better separation)
        self.otp_obj, self.otp_code = OTP.create_otp(user, "register")
        send_otp_email_web.delay(user.email, self.otp_code)

        return email