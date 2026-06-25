from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'phone', 'district', 'school_name', 'profile_picture', 'is_verified', 'referral_code', 'referred_by')
    readonly_fields = ('referral_code',)


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', 'profile__district')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'district', 'school_name', 'is_verified', 'created_at')
    list_filter = ('role', 'district', 'is_verified')
    search_fields = ('user__email', 'user__first_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
