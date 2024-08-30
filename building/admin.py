from django.contrib import admin

from building.models import Building, Entrance, Apartment, Bill, ApartmentBill


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('number', 'address')


@admin.register(Entrance)
class EntranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'building')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = (
        'owner_name', 'number', 'building', 'entrance', 'floor'
    )
    list_filter = ('owner', 'building', 'floor')
    search_fields = ('number', 'owner__first_name', 'owner__last_name')

    def owner_name(self, obj):
        return obj.owner.full_name()


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'for_month', 'total_electricity', 'total_cleaning', 'total_elevator_electricity', 'total_elevator_maintenance',
        'total_entrance_maintenance')
    list_filter = ('for_month',)
    search_fields = ('for_month',)
    list_display_links = ('for_month', 'total_electricity')


@admin.register(ApartmentBill)
class ApartmentBillAdmin(admin.ModelAdmin):
    list_display = ('apartment', 'owner_name', 'electricity', 'elevator_electricity', 'cleaning', 'elevator_maintenance',
                    'entrance_maintenance', 'total_bill', 'change', 'for_month', 'is_paid')
    list_filter = ('apartment', 'for_month', 'is_paid')
    search_fields = ('apartment__number', 'apartment__owner__first_name', 'apartment__owner__last_name')
    list_display_links = ('apartment', 'owner_name')

    def apartment(self, obj):
        return obj.apartment.number

    def owner_name(self, obj):
        return obj.apartment.owner.full_name()


admin.site.site_header = 'Building Management'
