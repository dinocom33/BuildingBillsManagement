from django.contrib import admin

from building.models import Building, Entrance, Apartment, Bill, ApartmentBill, Expense, TotalMaintenanceAmount


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ('number', 'address')


@admin.register(Entrance)
class EntranceAdmin(admin.ModelAdmin):
    list_display = ('name', 'building')


@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = (
        'owner_name', 'owner_email', 'number', 'building', 'entrance', 'floor'
    )
    list_filter = ('owner', 'building', 'floor')
    search_fields = ('number', 'owner__first_name', 'owner__last_name')

    def owner_name(self, obj):
        return obj.owner.full_name()

    def owner_email(self, obj):
        return obj.owner.email


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        'for_month', 'total_electricity', 'total_cleaning', 'total_elevator_electricity', 'total_elevator_maintenance',
        'total_entrance_maintenance', 'building', 'entrance')
    list_filter = ('for_month',)
    search_fields = ('for_month',)
    list_display_links = ('for_month', 'total_electricity')


@admin.register(ApartmentBill)
class ApartmentBillAdmin(admin.ModelAdmin):
    list_display = ('apartment', 'owner_name', 'building', 'entrance', 'electricity', 'elevator_electricity', 'cleaning', 'elevator_maintenance',
                    'entrance_maintenance', 'total_bill', 'change', 'for_month', 'is_paid')
    list_filter = ('apartment__building__number', 'apartment__entrance__name', 'for_month', 'is_paid')
    search_fields = ('apartment__number', 'apartment__owner__first_name', 'apartment__owner__last_name')
    list_display_links = ('apartment', 'owner_name')

    def apartment(self, obj):
        return obj.apartment.number

    def owner_name(self, obj):
        return obj.apartment.owner.full_name()

    def building(self, obj):
        return obj.apartment.building

    def entrance(self, obj):
        return obj.apartment.entrance


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost', 'maintenance_total_amount', 'description', 'for_month', 'building', 'entrance')
    list_filter = ('for_month', 'building', 'entrance')
    search_fields = ('name', 'for_month')
    list_display_links = ('name', 'cost')


@admin.register(TotalMaintenanceAmount)
class TotalMaintenanceAmountAdmin(admin.ModelAdmin):
    list_display = ('amount', 'for_month', 'building', 'entrance')
    list_filter = ('building__number', 'entrance__name', 'for_month')
    search_fields = ('building__number', 'entrance__name', 'for_month')
    list_display_links = ('amount', 'for_month')

    def building(self, obj):
        return obj.apartment.building

    def entrance(self, obj):
        return obj.apartment.entrance

admin.site.site_header = 'Building Management System Admin Panel'
