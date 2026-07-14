from django.urls import path
from store.views import HomeView, ProductView, GetVariantBySizeView, GetVariantByColorView
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product/detail/<str:slug>/<int:id>/', ProductView.as_view(), name='product-detail'),
    path('get/variant/by/size/', GetVariantBySizeView.as_view(), name='get-variant-by-size'),
    path('get/variant/by/color/', GetVariantByColorView.as_view(), name='get-variant-by-color'),
]