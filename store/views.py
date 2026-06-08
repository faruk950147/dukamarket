from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.contrib.sites.shortcuts import get_current_site
import logging

# import from local
from mixins.mixing import LoginRequiredMixin, LogoutRequiredMixin

logger = logging.getLogger('project')

# Create your views here.
@method_decorator(never_cache, name='dispatch')
class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        current_site = get_current_site(request)
        print("Current Site: ", current_site.domain)
        logger.info(f"Home page accessed by user: {request.user.username}")
        messages.success(request, f'Welcome to our store for user: {request.user.username}')
        print("Custom Host: ", request.get_host())
        return render(request, 'store/home.html')
    
class ProductView(LoginRequiredMixin, View):
    def get(self, request):
        current_site = get_current_site(request)
        print("Current Site: ", current_site.domain)

        logger.info(f"Product page accessed by user: {request.user.username}")
        messages.success(request, f'Product details page loaded for user: {request.user.username}')
        return render(request, 'store/product-detail.html')

