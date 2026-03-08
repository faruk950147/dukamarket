from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# import from account app
from account.forms import SignupForm, LoginForm
from account.mixing import LoginRequiredMixin, LogoutRequiredMixin
import logging
logger = logging.getLogger('project') 


# Signup View
@method_decorator(never_cache, name='dispatch')
class SignupView(View):
    def get(self, request):
        
        return render(request, 'account/signup.html')
    
    def post(self, request):
        
        return render(request, 'account/signup.html')

# Login View
@method_decorator(never_cache, name='dispatch')
class LoginView(View):
    def get(self, request):
        
        return render(request, 'account/login.html')
    
    def post(self, request):
        
        return render(request, 'account/login.html')

# Logout View
@method_decorator(never_cache, name='dispatch')
class LogoutView(View):
    def get(self, request):
        try:
            logout(request)
            logger.info(f"User logged out: {request.user.username} ({request.user.id})")
            messages.success(request, f"{request.user.username} have been logged out successfully.")
        except Exception as e:
            logger.error(f"Logout error: {e}")
            messages.error(request, f"Logout error: {e}")
        return redirect('login')


