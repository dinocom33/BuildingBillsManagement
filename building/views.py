import os

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.decorators import group_required
from accounts.views import get_building_entrance_apartments
from .tasks import create_apartment_bill_task

from building.models import Building, Bill, Apartment, Entrance, ApartmentBill

User = get_user_model()


@login_required
@group_required('manager')
def create_building(request):
    if request.method == 'POST':
        number = request.POST['number']
        address = request.POST['address']
        building = Building.objects.create(number=number, address=address)
        return redirect('building:create_entrance')
    return render(request, 'building/create_building.html')


@login_required
@group_required('manager')
def create_entrance(request):
    if request.method == 'POST':
        name = request.POST['name']
        building = request.POST['building']
        building_id = Building.objects.filter(number=building).first().id
        print(building_id)
        entrance = Entrance.objects.create(name=name, building_id=building_id)
        return redirect('building:create_entrance')

    return render(request, 'building/create_entrance.html')


@login_required
@group_required('manager')
def create_apartment(request):
    if request.method == 'POST':
        building = request.POST['building']
        entrance = request.POST['entrance']
        owner = request.POST['owner']
        floor = request.POST['floor']
        number = request.POST['number']

        try:
            building_id = Building.objects.filter(number=building).first().id
            entrance_id = Entrance.objects.filter(name=entrance).first().id
            owner_id = User.objects.filter(email=owner).first().id
        except AttributeError:
            messages.error(request, 'Invalid data')
            return redirect('building:create_apartment')

        if Apartment.objects.filter(building__id=building_id, entrance__id=entrance_id, number=number).exists():
            messages.error(request, 'Apartment already exists')
            return redirect('building:create_apartment')

        Apartment.objects.create(building_id=building_id, entrance_id=entrance_id, owner_id=owner_id, floor=floor,
                                 number=number)
        return redirect('building:create_apartment')

    return render(request, 'building/create_apartment.html')


@login_required
@group_required('manager')
def create_bill(request):
    if request.method == 'POST':
        user = request.user
        total_electricity = request.POST['total_electricity']
        total_cleaning = request.POST['total_cleaning']
        total_elevator_electricity = request.POST['total_elevator_electricity']
        total_elevator_maintenance = request.POST['total_elevator_maintenance']
        total_entrance_maintenance = request.POST['total_entrance_maintenance']
        building = user.owner.filter(entrance__isnull=False).first().entrance.building
        entrance = user.owner.filter(entrance__isnull=False).first().entrance
        for_month = request.POST['for_month']

        building_id = Building.objects.filter(number=building.number).first().id
        entrance_id = Entrance.objects.filter(name=entrance.name).first().id

        if Bill.objects.filter(for_month=for_month, building__id=building_id, entrance__id=entrance_id).exists():
            messages.error(request, 'Bill already exists')
            return redirect('building:create_bill')

        Bill.objects.create(
            total_electricity=float(total_electricity),
            total_cleaning=float(total_cleaning),
            total_elevator_electricity=float(total_elevator_electricity),
            total_elevator_maintenance=float(total_elevator_maintenance),
            total_entrance_maintenance=float(total_entrance_maintenance),
            building_id=building_id,
            entrance_id=entrance_id,
            for_month=for_month
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

            electricity = float(total_electricity) / len(apartments)
            cleaning = float(total_cleaning) / len(apartments)
            elevator_electricity = float(total_elevator_electricity) / len(apartments)
            elevator_maintenance = float(total_elevator_maintenance) / len(apartments)
            entrance_maintenance = float(total_entrance_maintenance) / len(apartments)

            email_subject = f'You have a new bill for your apartment {apartment.number}'
            email_message = (
                f'You have a new bill for apartment {apartment.number} '
                f'for the month {for_month} as follows: \n'
                f'Electricity: {electricity:.2f}lv \n'
                f'Cleaning: {cleaning:.2f}lv \n'
                f'Elevator electricity: {elevator_electricity:.2f}lv \n'
                f'Elevator maintenance: {elevator_maintenance:.2f}lv \n'
                f'Entrance maintenance: {entrance_maintenance:.2f}lv \n'
                f'Total sum: {(electricity + cleaning + elevator_electricity + elevator_maintenance + entrance_maintenance):.2f}lv'
            )
            from_email = os.getenv('EMAIL_HOST_USER')
            recipient_list = [apartment.owner.email]

            create_apartment_bill_task.delay(
                apartment.id,
                for_month,
                electricity,
                cleaning,
                elevator_electricity,
                elevator_maintenance,
                entrance_maintenance,
                last_change,
                email_subject,
                email_message,
                from_email,
                recipient_list
            )

        messages.success(request, 'Bill created successfully')
        return redirect('building:create_bill')

    return render(request, 'building/create_bill.html')


@login_required
@group_required('manager')
def apartments(request):
    entrance = request.user.owner.filter(entrance__isnull=False).first().entrance
    all_apartments = Apartment.objects.filter(entrance=entrance)

    context = {
        'apartments': all_apartments,
        'entrance': entrance
    }
    return render(request, 'building/apartments.html', context)
