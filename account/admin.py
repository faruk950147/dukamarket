from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'country', 'city', 'home_city', 'zip_code', 'address', 'is_active', 'is_superuser', 'is_staff', 'created_at', 'updated_at', 'image_tag')
    search_fields = ('username', 'email', 'phone')
    ordering = ('id',)


admin.site.register(User, UserAdmin)