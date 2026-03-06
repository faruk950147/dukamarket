from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout

# import from account app
from .forms import SignupForm, LoginForm


# Create your views here.
class SignupView(View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'account/signup.html', {'form': form})   
    
class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'account/login.html', {'form': form})
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')