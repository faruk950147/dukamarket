from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from account.models import User, OTP

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'phone', 'country', 'city', 'home_city', 'zip_code', 
                    'address', 'is_active', 'is_superuser', 'is_staff', 'is_verified', 'created_at', 
                    'updated_at', 'last_login', 'image_tag')
    search_fields = ('username', 'email', 'phone')
    ordering = ('id',)
    # static readonly fields
    readonly_fields = ('image_tag', 'last_login') # you can add more fields here

    fieldsets = (
        (None, {'fields': ('username', 'email', 'phone', 'password', 'country', 
                           'city', 'home_city', 'zip_code', 'address', 'image_tag')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'is_staff', 'is_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2', 'country', 'city', 
                       'home_city', 'zip_code', 'address', 'image_tag'),
        }),
    )

    # dynamic readonly fields
    def get_readonly_fields(self, request, obj=None):
        # if obj exists (i.e., edit mode)
        if obj:
            # you can add more fields here
            return self.readonly_fields + ('id', 'username', 'email', 'phone', 'password1', 'password2', 
                                    'country', 'city', 'home_city', 'zip_code', 'address', 'image_tag')
        return self.readonly_fields  # new create

admin.site.register(User, UserAdmin)

class OTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'otp_type', 'otp_hash', 'otp_salt', 'is_used', 'used_count', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('id',)
    
    def get_readonly_fields(self, request, obj=None):
        return ('id', 'user', 'otp_type', 'otp_hash', 'otp_salt', 'is_used', 'used_count', 'created_at')

admin.site.register(OTP, OTPAdmin)

