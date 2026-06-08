from django.urls import path
from store.api_views import *

urlpatterns = [
    path('', HomeViewAPI.as_view()),
]