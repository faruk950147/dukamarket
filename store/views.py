from django.shortcuts import render
from django.views import View
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger('project')

# Create your views here.
@method_decorator(never_cache, name='dispatch')
class HomeView(View):
    def get(self, request):
        logger.info(f"Home page accessed by user: {request.user.username}")
        messages.success(request, f'Welcome to our store for user: {request.user.username}')
        return render(request, 'store/home.html')

@method_decorator(never_cache, name='dispatch')
class ProductDetailView(View):
    def get(self, request):
        logger.info(f"Product page accessed by user: {request.user.username}")
        messages.success(request, f'Product details page loaded for user: {request.user.username}')
        return render(request, 'store/product-detail.html')

