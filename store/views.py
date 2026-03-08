from django.shortcuts import render
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

# custom import
import logging
logger = logging.getLogger('project')

@method_decorator(never_cache, name='dispatch')
class HomeView(View):
    def get(self, request):
        logger.info(f"")
        messages.success(request, f'Home page loaded')
        return render(request, 'store/home.html')
    
class ProductDetailView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'store/product-detail.html')

