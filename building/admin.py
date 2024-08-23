from django.contrib import admin

from building.models import Building, Entrance, Apartment


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('number', 'address', 'num_of_entrances')


@admin.register(Entrance)
class EntranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'floors', 'num_of_apartments')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'building', 'entrance', 'floor')

admin.site.site_header = 'Building Management'