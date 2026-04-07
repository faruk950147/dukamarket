from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import User

class UserAdmin(BaseUserAdmin):
    model = User

    # List view: display all important fields including image and online status
    list_display = (
        "username", "email", "phone", "image_tag", "country", "city", "home_city", "zip_code", "address",
        "is_active", "is_staff", "is_verified", "is_superuser",
        "online_status", "last_seen", "last_active",
        "created_at", "updated_at"
    )

    # Filters on the sidebar
    list_filter = ("is_active", "is_staff", "is_verified", "is_superuser", "is_online")

    # Searchable fields
    search_fields = ("username", "email", "phone", "city", "country")

    # Default ordering
    ordering = ("-created_at",)

    # Fields that are readonly in detail view
    readonly_fields = ("last_seen", "last_active", "image_tag", "created_at", "updated_at", "last_login")

    # Grouping fields in the admin detail view
    fieldsets = (
        (None, {"fields": ("username", "email", "phone", "password")}),
        ("Profile Info", {"fields": ("image", "country", "city", "home_city", "zip_code", "address")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_verified", "groups", "user_permissions")}),
        ("Status", {"fields": ("is_online", "last_seen", "last_active")}),
        ("Important Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    # Fields for creating a new user
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "phone", "password1", "password2", "is_active", "is_staff", "is_verified"),
        }),
    )

    # Make certain fields readonly after creation
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("username", "email", "phone")
        return self.readonly_fields

    # Admin actions for multiple user selection
    actions = ["mark_selected_online", "mark_selected_offline"]

    def mark_selected_online(self, request, queryset):
        queryset.update(is_online=True, last_seen=timezone.now())
    mark_selected_online.short_description = "Mark selected users as Online"

    def mark_selected_offline(self, request, queryset):
        queryset.update(is_online=False, last_seen=timezone.now())
    mark_selected_offline.short_description = "Mark selected users as Offline"

    # Optional: show online/offline as colored badge
    def online_status(self, obj):
        color = "green" if obj.is_online else "red"
        status = "Online" if obj.is_online else "Offline"
        return format_html('<b style="color:{}">{}</b>', color, status)
    online_status.short_description = "Status"

# Register the custom User model with admin
admin.site.register(User, UserAdmin)
