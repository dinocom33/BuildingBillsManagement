import os
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View

from accounts.decorators import group_required
from ensure_celery_running import ensure_celery_running
from .tasks import create_apartment_bills_task, send_message_email_task

from building.models import Building, Bill, Apartment, Entrance, Expense, TotalMaintenanceAmount, Message

User = get_user_model()


@login_required
@group_required('manager')
def create_building(request):
    if request.method == 'POST':
        user = request.user
        number = request.POST['number']
        address = request.POST['address']

        if Building.objects.filter(number=number, address=address).exists():
            messages.error(request, 'Building already exists')
            return redirect('building:apartments')

        if user.owner.filter(entrance__isnull=False).exists():
            messages.error(request, 'You already have a building')
            return redirect('building:apartments')

        Building.objects.create(number=number, address=address)

        messages.success(request, 'Building created successfully')
        return redirect('building:apartments')
    return render(request, 'building/apartments.html')


@login_required
@group_required('manager')
def create_entrance(request):
    if request.method == 'POST':
        # Get the current user
        user = request.user

        # Extract entrance details
        name = request.POST['name']
        building_number = request.POST['building']

        try:
            # Find the building
            building = Building.objects.get(number=building_number)
        except Building.DoesNotExist:
            messages.error(request, 'Building does not exist')
            return redirect('building:apartments')

        # Check if entrance already exists for this building
        if Entrance.objects.filter(name=name, building=building).exists():
            messages.error(request, 'Entrance already exists in this building')
            return redirect('building:apartments')

        # Create the first entrance
        try:
            # Create a new entrance directly
            entrance = Entrance.objects.create(
                name=name,
                building=building
            )

            messages.success(request, 'Entrance created successfully')
            return redirect('building:apartments')

        except Exception as e:
            messages.error(request, f'Error creating entrance: {str(e)}')
            return redirect('building:apartments')

    return render(request, 'building/apartments.html')


@login_required
@group_required('manager')
def create_apartment(request):
    if request.method == 'POST':
        user = request.user
        building = request.POST['building']
        entrance = request.POST['entrance']
        owner = request.POST['owner']
        floor = request.POST['floor']
        number = request.POST['number']

        try:
            # Use get() instead of filter().first() for more precise error handling
            building_obj = Building.objects.get(number=building)
            entrance_obj = Entrance.objects.get(name=entrance, building=building_obj)
            owner_obj = User.objects.get(email=owner)
        except (Building.DoesNotExist, Entrance.DoesNotExist, User.DoesNotExist):
            messages.error(request, 'Invalid data')
            return redirect('building:apartments')

        # Verify that the entrance belongs to the building
        if entrance_obj.building != building_obj:
            messages.error(request, 'Entrance does not belong to this building')
            return redirect('building:apartments')

        # Check if apartment already exists
        if Apartment.objects.filter(
                building=building_obj,
                entrance=entrance_obj,
                number=number
        ).exists():
            messages.error(request, 'Apartment already exists')
            return redirect('building:apartments')

        # Create the apartment
        Apartment.objects.create(
            building=building_obj,
            entrance=entrance_obj,
            owner=owner_obj,
            floor=floor,
            number=number
        )

        messages.success(request, 'Apartment created successfully')
        return redirect('building:apartments')

    return render(request, 'building/apartments.html')


@login_required
@group_required('manager')
def apartments(request):
    try:
        # Get all entrances associated with the user
        entrances = (
            request.user.owner
            .select_related('entrance__building')
            .filter(entrance__isnull=False)
            .values_list('entrance', flat=True)
        )

        # If no entrances exist, create an empty queryset
        if not entrances:
            # Find apartments created by the current user
            all_apartments = Apartment.objects.filter(
                building__in=Building.objects.filter(
                    entrance__apartments__isnull=False
                )
            ).distinct()
        else:
            # Filter apartments that belong to the user's entrances
            all_apartments = Apartment.objects.filter(entrance__in=entrances)

        # Additional filtering to ensure apartments are associated with user's context
        all_apartments = all_apartments.select_related(
            'building',
            'entrance',
            'owner'
        ).order_by('entrance__name', 'number')

    except Exception as e:
        # Handle any potential errors
        messages.error(request, f'Error loading apartments: {str(e)}')
        all_apartments = Apartment.objects.none()

    context = {
        'apartments': all_apartments,
        'entrances': entrances
    }
    return render(request, 'building/apartments.html', context)


@login_required
@group_required('manager')
def bills(request):
    try:
        # Optimize the query to reduce database hits
        owner = (
            request.user.owner
            .select_related('entrance__building')
            .filter(entrance__isnull=False)
            .first()
        )

        # Handle case where no entrance exists
        if not owner or not owner.entrance:
            context = {
                'building': None,
                'entrance': None,
                'bills': [],
                'no_data': True
            }
            messages.info(request, 'No building or entrance found.')
            return render(request, 'building/bills.html', context)

        # Get building and entrance
        building = owner.entrance.building
        entrance = owner.entrance

        # Query bills with additional optimization
        all_bills = Bill.objects.filter(
            building=building,
            entrance=entrance
        ).order_by('-for_month')


        # Paginate bills
        paginator = Paginator(all_bills, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'building': building,
            'entrance': entrance,
            'bills': page_obj,
            'no_data': len(page_obj) == 0
        }

        # Add a message if no bills exist
        if len(page_obj) == 0:
            messages.info(request, 'No bills found for this entrance.')

    except Exception as e:
        # Handle any unexpected errors
        context = {
            'building': None,
            'entrance': None,
            'bills': [],
            'error': str(e)
        }
        messages.error(request, f'An error occurred: {str(e)}')

    return render(request, 'building/bills.html', context)


class CreateBillView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'building/bills.html'
    login_url = 'login'

    def test_func(self):
        """
        Restricts access to users belonging to the 'manager' group or superusers.
        """
        return self.request.user.groups.filter(name='manager').exists() or self.request.user.is_superuser

    @method_decorator(ensure_celery_running)
    def post(self, request, *args, **kwargs):
        user = request.user

        # Extract data from POST
        total_electricity = request.POST.get('total_electricity')
        total_cleaning = request.POST.get('total_cleaning')
        total_elevator_electricity = request.POST.get('total_elevator_electricity')
        total_elevator_maintenance = request.POST.get('total_elevator_maintenance')
        total_entrance_maintenance = request.POST.get('total_entrance_maintenance')
        for_month = request.POST.get('for_month', '').strip()

        # Validate and process month input
        try:
            current_month = datetime.strptime(for_month[:7], "%Y-%m")
        except ValueError as e:
            messages.error(request, f'Invalid month format: {e}')
            return redirect('building:bills')

        next_month = current_month + relativedelta(months=1)
        previous_month = current_month - relativedelta(months=1)
        previous_month_str = previous_month.strftime("%Y-%m")
        next_month_str = next_month.strftime("%Y-%m")

        # Fetch building and entrance
        owner_apartment = user.owner.filter(entrance__isnull=False).first()
        if not owner_apartment:
            messages.error(request, 'You do not have a valid entrance or building.')
            return redirect('building:bills')

        building = owner_apartment.entrance.building
        entrance = owner_apartment.entrance

        building_id = building.id
        entrance_id = entrance.id

        # Check if the bill already exists
        if Bill.objects.filter(for_month=for_month, building_id=building_id, entrance_id=entrance_id).exists():
            messages.error(request, 'Bill already exists.')
            return redirect('building:bills')

        # Create the bill
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

        # Get maintenance amount from previous month first
        previous_maintenance_amount = TotalMaintenanceAmount.objects.filter(
            building=building,
            entrance=entrance,
            for_month=previous_month_str
        ).order_by('-id').first()

        # If previous month exists, use that amount, otherwise use the current total_entrance_maintenance
        maintenance_amount = (
            previous_maintenance_amount.amount
            if previous_maintenance_amount
            else Decimal(total_entrance_maintenance)
        )

        # Create or update current month's maintenance amount
        current_maintenance_amount, created = TotalMaintenanceAmount.objects.get_or_create(
            building=building,
            entrance=entrance,
            for_month=for_month,
            defaults={'amount': maintenance_amount}
        )

        # Create maintenance amount for the next month
        # TotalMaintenanceAmount.objects.create(
        #     amount=maintenance_amount,
        #     building_id=building_id,
        #     entrance_id=entrance_id,
        #     for_month=next_month_str,
        # )

        # Prepare data for apartment bills and notifications
        apartments = Apartment.objects.filter(entrance=entrance)
        if not apartments.exists():
            messages.error(request, 'No apartments found for this entrance.')
            return redirect('building:bills')

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

        # Trigger asynchronous task for creating apartment bills
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

        messages.success(request, 'Bill created successfully.')
        return redirect('building:bills')

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request to render the bill creation page.
        """
        return render(request, self.template_name)


@login_required
def manage_expenses(request):
    now = datetime.now()

    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    if selected_month and selected_year:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
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
    try:
        building = user.owner.filter(entrance__isnull=False).first().entrance.building
        entrance = user.owner.filter(entrance__isnull=False).first().entrance
        total_maintenance_amount = TotalMaintenanceAmount.objects.filter(building=building, entrance=entrance,
                                                                         for_month__month=selected_month,
                                                                         for_month__year=selected_year).order_by(
            '-id').first()
        expenses = Expense.objects.filter(building=building, entrance=entrance,
                                          for_month__month=selected_month,
                                          for_month__year=selected_year).order_by(
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
    except AttributeError:
        building = None
        entrance = None
        total_maintenance_amount = None
        expenses = []
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
        total_maintenance_amount.amount -= Decimal(cost)
        total_maintenance_amount.save()

        # Create the expense record
        Expense.objects.create(
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


@login_required
@group_required('manager')
@ensure_celery_running
def add_message(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        text = request.POST.get('text', '').strip()
        uploaded_file = request.FILES.get('file', None)
        user = request.user
        building = user.owner.filter(entrance__isnull=False).first().entrance.building
        entrance = user.owner.filter(entrance__isnull=False).first().entrance
        all_residents = User.objects.filter(owner__entrance=entrance)

        # Validate file type
        if uploaded_file:
            valid_mime_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'image/jpeg',
                'image/png',
            ]

            if uploaded_file.content_type not in valid_mime_types:
                messages.error(request, 'Invalid file type. Allowed types: PDF, Word, Images.')
                return redirect('building:messages')

        # Create and save the message
        message = Message.objects.create(
            title=title,
            text=text,
            building=building,
            entrance=entrance,
            file=uploaded_file
        )

        email_subject = f'New message from {building.number} building'
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        dashboard_link = f'{protocol}://{domain}/building/messages/'

        # Render the HTML email template
        email_html_message = render_to_string('building/new_message_email.html', {
            'title': title,
            'text': text,
            'file': uploaded_file,
            'building': building,
            'entrance': entrance,
            'dashboard_link': dashboard_link,
        })

        # Send email task
        send_message_email_task.delay(
            email_subject,
            email_html_message,
            from_email=os.getenv('EMAIL_HOST_USER'),
            recipient_list=[resident.email for resident in all_residents]
        )

        messages.success(request, 'Message created and email sent successfully')
        return redirect('building:messages')

    return render(request, 'building/messages.html')


@login_required
def messages_view(request):
    all_messages = Message.objects.filter(building__apartments__owner=request.user).order_by('-date')

    paginator = Paginator(all_messages, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'all_messages': page_obj
    }

    return render(request, 'building/messages.html', context)


@login_required
def message_view(request, message_id):
    message = Message.objects.get(id=message_id)

    context = {
        'message': message
    }

    return render(request, 'building/messages.html', context)
