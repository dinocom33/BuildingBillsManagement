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
    list_display = ('number', 'building', 'entrance', 'floor')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
    'apartment', 'electricity', 'cleaning', 'elevator_electricity', 'elevator_maintenance', 'entrance_maintenance',
    'total_bill')
    list_filter = ('apartment',)
    search_fields = ('apartment__number',)

    def apartment(self, obj):
        return obj.apartment


admin.site.site_header = 'Building Management'
