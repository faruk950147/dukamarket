from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q

User = get_user_model()


# Signup Form
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )
    password2 = forms.CharField(
        min_length=8,
        max_length=128,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone']

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')
        if not email and not phone:
            raise forms.ValidationError("Email or Phone must be provided!")
        return cleaned_data

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# Login Form (Username / Email / Phone)
class LoginForm(forms.Form):
    login = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or Email or Phone'}),
        label="Username or Email or Phone"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Try to find user by username / email / phone
            user_qs = User.objects.filter(Q(username=username) | Q(email=username) | Q(phone=username))
            if not user_qs.exists():
                raise forms.ValidationError("Invalid login credentials")
            user = user_qs.first()
            if not user.check_password(password):
                raise forms.ValidationError("Invalid login credentials")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive")
            cleaned_data['user'] = user
        return cleaned_data