from django.urls import path
from store.views import HomeView, ProductView
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product-detail/', ProductView.as_view(), name='product-detail'),
]