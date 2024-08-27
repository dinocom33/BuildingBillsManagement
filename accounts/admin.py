# from django.contrib import admin
# from django.contrib.auth import get_user_model
#
# from building.models import Apartment
#
# User = get_user_model()
#
#
# def full_name(obj):
#     return f"{obj.first_name} {obj.last_name}"
#
#
# def building(obj):
#     return obj.building
#
#
# def entrance(obj):
#     return obj.entrance
#
#
# def apartment(obj):
#     return obj.apartment
#
#
# @admin.register(User)
# class UserAdmin(admin.ModelAdmin):
#     list_display = ('full_name', 'email', 'is_staff', 'is_superuser', 'building', 'entrance', 'get_apartment')
#     list_filter = ('is_staff', 'is_superuser', 'building', 'entrance')
#     search_fields = ('email', 'first_name', 'last_name', 'building__number', 'entrance__name')
#     list_display_links = ('full_name', 'email')
#
#     def get_apartment(self, obj):
#         return Apartment.objects.filter(owner=obj).first()
#
#     get_apartment.short_description = 'Apartment'
#
# # admin.site.unregister(User)
# # admin.site.register(User, UserAdmin)


from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("full_name", "email", "is_staff", "is_active",)
    list_filter = ("email", "is_staff", "is_active",)
    list_display_links = ("full_name", "email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "first_name", "last_name", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


admin.site.register(User, CustomUserAdmin)
