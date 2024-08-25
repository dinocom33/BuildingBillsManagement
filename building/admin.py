from django.contrib import admin

from building.models import Building, Entrance, Apartment, Bill


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('number', 'address', 'num_of_entrances')


@admin.register(Entrance)
class EntranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'floors', 'num_of_apartments')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'building', 'entrance', 'floor', 'owner_name')

    def owner_name(self, obj):
        return obj.owner.full_name()


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
    'apartment', 'electricity', 'cleaning', 'elevator_electricity', 'elevator_maintenance', 'entrance_maintenance',
    'total_bill', 'for_month', 'is_paid')
    list_filter = ('apartment', 'for_month', 'is_paid')
    search_fields = ('apartment__number', 'for_month', 'is_paid')

    def apartment(self, obj):
        return obj.apartment


admin.site.site_header = 'Building Management'
