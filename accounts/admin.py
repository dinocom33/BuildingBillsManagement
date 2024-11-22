from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from building.models import Apartment
from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("full_name", "email", "get_groups", "is_staff", "is_active", "get_apartment")
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

    def get_groups(self, obj):
        return ", ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = 'Groups'

    def get_apartment(self, obj):
        apartment = Apartment.objects.filter(owner=obj).first()
        return apartment

    get_apartment.short_description = 'Apartment'


admin.site.register(User, CustomUserAdmin)
