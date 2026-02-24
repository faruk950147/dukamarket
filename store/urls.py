from django.urls import path
from store.views import (
    HomeView, ProductDetailView
)
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product-detail/', ProductDetailView.as_view(), name='product-detail'),
]