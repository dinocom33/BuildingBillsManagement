from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'building', 'entrance', 'apartment')
    list_filter = ('is_staff', 'is_superuser', 'building', 'entrance', 'apartment')
    search_fields = ('email', 'first_name', 'last_name', 'building__number', 'entrance__name', 'apartment__number')

    def building(self, obj):
        return obj.building

    def entrance(self, obj):
        return obj.entrance

    def apartment(self, obj):
        return obj.apartment


# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)