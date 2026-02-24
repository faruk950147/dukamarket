from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import logout


# Create your views here.
class SignupView(View):
    def get(self, request):
        return render(request, 'account/signup.html')
    
class LoginView(View):
    def get(self, request):
        return render(request, 'account/login.html')
    
class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')