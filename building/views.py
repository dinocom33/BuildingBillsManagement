import os
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from accounts.decorators import group_required
from .tasks import create_apartment_bills_task

from building.models import Building, Bill, Apartment, Entrance, Expense, TotalMaintenanceAmount

User = get_user_model()


@login_required
@group_required('manager')
def create_building(request):
    if request.method == 'POST':
        number = request.POST['number']
        address = request.POST['address']
        Building.objects.create(number=number, address=address)
        return redirect('building:apartments')
    return render(request, 'building/apartments.html')


@login_required
@group_required('manager')
def create_entrance(request):
    if request.method == 'POST':
        name = request.POST['name']
        building = request.POST['building']
        building_id = Building.objects.filter(number=building).first().id
        print(building_id)
        Entrance.objects.create(name=name, building_id=building_id)
        return redirect('building:apartments')

    return render(request, 'building/apartments.html')


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
        return redirect('building:apartments')

    return render(request, 'building/apartments.html')


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
        for_month = request.POST['for_month'].strip()

        try:
            current_month = datetime.strptime(for_month[:7], "%Y-%m")
        except ValueError as e:
            messages.error(request, f'Invalid month format: {e}')
            return redirect('building:create_bill')

        next_month = current_month + relativedelta(months=1)
        next_month_str = next_month.strftime("%Y-%m")

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

        total_maintenance_amount = TotalMaintenanceAmount.objects.filter(
            building=building,
            entrance=entrance,
            for_month=for_month
        ).order_by('-id').first()

        if not total_maintenance_amount:
            total_maintenance_amount = TotalMaintenanceAmount.objects.create(
                amount=Decimal(total_entrance_maintenance),
                building_id=building_id,
                entrance_id=entrance_id,
                for_month=for_month,
            )

        TotalMaintenanceAmount.objects.create(
            amount=total_maintenance_amount.amount + Decimal(total_entrance_maintenance),
            building_id=building_id,
            entrance_id=entrance_id,
            for_month=next_month_str,
        )

        apartments = Apartment.objects.filter(entrance=entrance)
        apartments_ids = list(apartments.values_list('id', flat=True))

        ap_el = float(total_electricity) / len(apartments)
        ap_clean = float(total_cleaning) / len(apartments)
        ap_elev_el = float(total_elevator_electricity) / len(apartments)
        ap_maint = float(total_elevator_maintenance) / len(apartments)
        entr_maint = float(total_entrance_maintenance) / len(apartments)

        email_subject_template = 'You have a new bill for your apartment {apartment_number}'
        email_message_template = (
            'You have a new bill for apartment {apartment_number} '
            'for {for_month} as follows: \n'
            'Electricity: {electricity:.2f}lv \n'
            'Cleaning: {cleaning:.2f}lv \n'
            'Elevator electricity: {elevator_electricity:.2f}lv \n'
            'Elevator maintenance: {elevator_maintenance:.2f}lv \n'
            'Entrance maintenance: {entrance_maintenance:.2f}lv \n'
            'Total sum: {total:.2f}lv'
        )

        from_email = os.getenv('EMAIL_HOST_USER')

        # Call the task to create bills for all apartments
        create_apartment_bills_task.delay(
            apartments_ids,
            for_month,
            ap_el,
            ap_clean,
            ap_elev_el,
            ap_maint,
            entr_maint,
            email_subject_template,
            email_message_template,
            from_email
        )

        messages.success(request, 'Bill created successfully')
        return redirect('dashboard')

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


@login_required
def manage_expenses(request):
    now = datetime.now()

    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    if selected_month and selected_year:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    else:
        if now.month == 1:
            selected_month = 12
            selected_year = now.year - 1
        else:
            selected_month = now.month
            selected_year = now.year

    if selected_month == 0:
        selected_month = 12
        selected_year -= 1
    elif selected_month == 13:
        selected_month = 1
        selected_year += 1

    user = request.user
    building = user.owner.filter(entrance__isnull=False).first().entrance.building
    entrance = user.owner.filter(entrance__isnull=False).first().entrance
    total_maintenance_amount = TotalMaintenanceAmount.objects.filter(building=building, entrance=entrance,
                                                                     for_month__month=selected_month).order_by(
        '-id').first()
    expenses = Expense.objects.filter(building=building, entrance=entrance, for_month__month=selected_month).order_by(
        '-id')

    if total_maintenance_amount:
        total_maintenance_amount = total_maintenance_amount.amount
    else:
        total_maintenance_amount = 0

    if request.method == 'POST':
        name = request.POST['name']
        cost = request.POST['cost']
        description = request.POST['description']
        for_month = request.POST['for_month']

        expense = Expense.objects.create(
            name=name,
            cost=float(cost),
            description=description,
            building=building,
            entrance=entrance,
            for_month=for_month,
        )

        total_maintenance_amount.amount -= expense.cost
        total_maintenance_amount.save()

        messages.success(request, 'Expense created successfully')
        return redirect('building:expense_dashboard', month=selected_month, year=selected_year)

    context = {
        'total_maintenance_amount': total_maintenance_amount,
        'month': selected_month,
        'year': selected_year,
        'building': building,
        'entrance': entrance,
        'expenses': expenses
    }

    return render(request, 'building/manage_expenses.html', context)


@login_required
@group_required('manager')
def create_expense(request):
    if request.method == 'POST':
        name = request.POST['name']
        cost = request.POST['cost']
        description = request.POST['description']
        for_month = request.POST['for_month']  # Format: 'YYYY-MM-DD'
        month = request.POST['month']
        year = request.POST['year']

        user = request.user
        building = user.owner.filter(entrance__isnull=False).first().entrance.building
        entrance = user.owner.filter(entrance__isnull=False).first().entrance

        # Step 1: Parse for_month (YYYY-MM-DD) and get the current date
        try:
            # Convert for_month into a datetime object (YYYY-MM-DD format)
            for_month_date = datetime.strptime(for_month, "%Y-%m-%d")

            # Get the current date
            current_date = datetime.today()

            # Extract year and month for both dates (ignore the day)
            current_year_month = current_date.strftime("%Y-%m")
            for_month_year_month = for_month_date.strftime("%Y-%m")
        except ValueError as e:
            messages.error(request, f'Invalid date format: {e}')
            return redirect(f'{reverse("building:expense_dashboard")}?month={month}&year={year}')

        # Step 2: Check if for_month is not in the current month
        if for_month_year_month != current_year_month:
            messages.error(request, 'Expenses for previous or future months cannot be created.')
            return redirect(f'{reverse("building:expense_dashboard")}?month={month}&year={year}')

        total_maintenance_amount = TotalMaintenanceAmount.objects.filter(building=building, entrance=entrance).order_by(
            '-id').first()

        if not total_maintenance_amount:
            messages.error(request, 'You have no funds')
            return redirect(f'{reverse("building:expense_dashboard")}?month={month}&year={year}')

        # Deduct the cost from the total maintenance amount
        total_maintenance_amount = TotalMaintenanceAmount.objects.create(
            amount=total_maintenance_amount.amount - Decimal(cost),
            building=building,
            entrance=entrance,
            for_month=for_month
        )
        total_maintenance_amount.save()

        # Create the expense record
        expense = Expense.objects.create(
            name=name,
            cost=float(cost),
            description=description,
            building=building,
            entrance=entrance,
            for_month=for_month,
            maintenance_total_amount=total_maintenance_amount
        )

        messages.success(request, 'Expense created successfully')
        return redirect(f'{reverse("building:expense_dashboard")}?month={month}&year={year}')

    return render(request, 'building/manage_expenses.html')
