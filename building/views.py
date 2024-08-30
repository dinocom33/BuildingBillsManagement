from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .tasks import send_email_task

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

        entrance = request.user.owner.filter(entrance__isnull=False).first().entrance
        apartments = Apartment.objects.filter(entrance=entrance)

        for apartment in apartments:
            last_bill = ApartmentBill.objects.filter(apartment=apartment).last()

            if last_bill is None:
                last_change = 0
            else:
                last_change = last_bill.change
                last_bill.change = 0
                last_bill.save()

            apartment_bill = ApartmentBill.objects.create(
                apartment=apartment,
                for_month=for_month,
                change=last_change,
                electricity=float(total_electricity) / len(apartments),
                cleaning=float(total_cleaning) / len(apartments),
                elevator_electricity=float(total_elevator_electricity) / len(apartments),
                elevator_maintenance=float(total_elevator_maintenance) / len(apartments),
                entrance_maintenance=float(total_entrance_maintenance) / len(apartments),
            )

            send_email_task.delay(
                subject=f'You have a new bill for your apartment {apartment_bill.apartment.number}',
                message=f'You have a new bill for apartment {apartment_bill.apartment.number}, '
                        f'for the month {for_month} as follows: \n'
                        f'Electricity: {apartment_bill.electricity:.2f}lv \n'
                        f'Cleaning: {apartment_bill.cleaning:.2f}lv \n'
                        f'Elevator electricity: {apartment_bill.elevator_electricity:.2f}lv \n'
                        f'Elevator maintenance: {apartment_bill.elevator_maintenance:.2f}lv \n'
                        f'Entrance maintenance: {apartment_bill.entrance_maintenance:.2f}lv \n'
                        f'Total sum: {apartment_bill.total_bill():.2f}lv',
                from_email='mycookbook787@gmail.com',
                recipient_list=[apartment.owner.email],
            )

        messages.success(request, 'Bill created successfully')
        return redirect('create_bill')

    return render(request, 'building/create_bill.html')
