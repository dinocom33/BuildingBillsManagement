from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from building.models import Building, Bill, Apartment, Entrance, ApartmentBill


@login_required
def create_bill(request):
    if request.method == 'POST':
        total_electricity = request.POST['total_electricity']
        total_cleaning = request.POST['total_cleaning']
        total_elevator_electricity = request.POST['total_elevator_electricity']
        total_elevator_maintenance = request.POST['total_elevator_maintenance']
        total_entrance_maintenance = request.POST['total_entrance_maintenance']
        for_month = request.POST['for_month']

        Bill.objects.create(
            total_electricity=float(total_electricity),
            total_cleaning=float(total_cleaning),
            total_elevator_electricity=float(total_elevator_electricity),
            total_elevator_maintenance=float(total_elevator_maintenance),
            total_entrance_maintenance=float(total_entrance_maintenance),
        )

        apartments = Apartment.objects.filter(entrance=request.user.owner.filter(entrance__isnull=False).first().entrance)
        for apartment in apartments:
            ApartmentBill.objects.create(
                apartment=apartment,
                for_month=for_month,
                electricity=float(total_electricity) / len(apartments),
                cleaning=float(total_cleaning) / len(apartments),
                elevator_electricity=float(total_elevator_electricity) / len(apartments),
                elevator_maintenance=float(total_elevator_maintenance) / len(apartments),
                entrance_maintenance=float(total_entrance_maintenance) / len(apartments),
            )

        messages.success(request, 'Bill created successfully')
        return redirect('create_bill')

    return render(request, 'building/create_bill.html')
