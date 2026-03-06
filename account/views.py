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

# Create your views here.

@method_decorator(never_cache, name='dispatch')
class SignupView(LogoutRequiredMixin, View):
    def get(self, request):
        form = SignupForm()
        return render(request, 'account/signup.html', {'form': form})   
    def post(self, request):
        pass
   
@method_decorator(never_cache, name='dispatch') 
class LoginView(LogoutRequiredMixin, View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'account/login.html', {'form': form})
    
    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    logger.info(f"User signed in: {user.username} ({user.id})")
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Your account is not activated yet.')
                    logger.warning(f"Inactive user attempted sign-in: {user.username} ({user.id})")
            else:
                messages.error(request, 'Invalid username or password.')
                logger.warning(f"Failed sign-in attempt for username: {username}")
        else:
            messages.error(request, 'Please correct the errors below.')
            logger.info("Sign-in form invalid")
        return render(request, 'account/sign-in.html', {'form': form})

@method_decorator(never_cache, name='dispatch')
class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('login')