from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.messages.context_processors import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from BuildingBillsManagement import settings
from accounts.decorators import group_required
from building.models import Apartment, ApartmentBill
from .tasks import send_email_task
from .tokens import generate_token

User = get_user_model()


def get_building_entrance_apartments(user):
    apartment = Apartment.objects.filter(owner=user).first()
    building = apartment.building
    entrance = apartment.entrance
    apartments = Apartment.objects.filter(building=building, entrance=entrance)

    return [apartment, building, entrance, apartments]


@login_required
@group_required('manager')
def register(request):
    if request.method == 'POST':

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if not first_name or not last_name or not email or not password or not password2:
            messages.error(request, 'All fields are required')
            return redirect('create_resident')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('create_resident')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('create_resident')

        new_user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password)

        new_user.is_active = False
        new_user.save()

        # subject = "Welcome to Our Building Bills Management System"
        # message = f"Hello {new_user.first_name}!\n\nThank you for registering on our website. Please confirm your email address to activate your account.\n\nRegards,\nThe Django Team"
        from_email = settings.EMAIL_HOST_USER
        to_list = [new_user.email]
        # send_mail(subject, message, from_email, to_list, fail_silently=True)
        # Send email confirmation link
        current_site = get_current_site(request)
        email_subject = "You are invited to join Building Bills Management System"
        message2 = render_to_string('email_confirmation.html', {
            'name': f'{new_user.first_name} {new_user.last_name}',
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': generate_token.make_token(new_user)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [new_user.email],
        )
        send_mail(email_subject, message2, from_email, to_list, fail_silently=True)


        messages.success(request, 'Account created successfully. Email has been sent with confirmation link')
        return redirect('create_resident')


    return render(request, 'accounts/register.html')


def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request)
        messages.success(request, "Your Account has been activated!!")
        return redirect('login')
    else:
        return render(request,'activation_failed.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        if not email or not password:
            messages.error(request, 'All fields are required')
            return redirect('login')

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            messages.error(request, 'Wrong username or password')
            return redirect('login')

        auth.login(request, user)
        messages.success(request, 'Login successful')
        return redirect('index')

    return render(request, 'accounts/login.html')


@login_required
def logout(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.success(request, 'Logout successful')
        return redirect('login')


@login_required
def dashboard(request):
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
            selected_month = now.month - 1
            selected_year = now.year

    if selected_month == 0:
        selected_month = 12
        selected_year -= 1
    elif selected_month == 13:
        selected_month = 1
        selected_year += 1

    user = request.user
    apartment = Apartment.objects.filter(owner=user).first()

    if not apartment:
        selected_month = now.month - 1
        selected_year = now.year
        messages.error(request, 'You have no building, entrance and apartment associated with your account')
        return render(request, 'accounts/dashboard.html', {'month': selected_month, 'year': selected_year})

    building = apartment.building
    entrance = apartment.entrance
    apartments = Apartment.objects.filter(building=building, entrance=entrance)

    apartment_bills = ApartmentBill.objects.filter(
        apartment__building=building,
        apartment__entrance=entrance,
        for_month__month=selected_month,
        for_month__year=selected_year
    )

    context = {
        'entrance': entrance,
        'apartments': apartments,
        'bills': apartment_bills,
        'month': selected_month,
        'year': selected_year,
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required
@group_required('manager')
def manager_dashboard(request):
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
            selected_month = now.month - 1
            selected_year = now.year

    if selected_month == 0:
        selected_month = 12
        selected_year -= 1
    elif selected_month == 13:
        selected_month = 1
        selected_year += 1

    user = request.user
    apartment = Apartment.objects.filter(owner=user).first()

    if not apartment:
        selected_month = now.month - 1
        selected_year = now.year
        messages.error(request, 'You have no building, entrance and apartment associated with your account')
        return render(request, 'accounts/dashboard.html', {'month': selected_month, 'year': selected_year})

    building, entrance, apartments = get_building_entrance_apartments(user)

    apartment_bills = ApartmentBill.objects.filter(
        apartment__building=building,
        apartment__entrance=entrance,
        for_month__month=selected_month,
        for_month__year=selected_year
    )

    context = {
        'entrance': entrance,
        'apartments': apartments,
        'bills': apartment_bills,
        'month': selected_month,
        'year': selected_year,
    }

    return render(request, 'accounts/manager_dashboard.html', context)


@login_required
@group_required('manager')
def pay_bill(request, bill_id):
    if request.method == 'POST':

        apartment_bill = ApartmentBill.objects.get(id=bill_id)
        given_sum = request.POST.get('sum')
        month = request.POST.get('month', '')
        year = request.POST.get('year', '')

        if not given_sum:
            messages.error(request, 'Sum is required')
            return redirect(f'{reverse("manager_dashboard")}?month={month}&year={year}')

        given_sum = float(given_sum) + float(apartment_bill.change)

        if given_sum <= 0:
            messages.error(request, 'Sum must be greater than 0')
            return redirect(f'{reverse("manager_dashboard")}?month={month}&year={year}')

        if given_sum < float(apartment_bill.total_bill()) - 0.001:
            messages.error(request, 'Sum must be greater than or equal to total bill')
            return redirect(f'{reverse("manager_dashboard")}?month={month}&year={year}')

        if apartment_bill.is_paid:
            messages.error(request, 'Bill already paid')
            return redirect(f'{reverse("manager_dashboard")}?month={month}&year={year}')

        if given_sum >= apartment_bill.total_bill():
            apartment_bill.change = given_sum - float(apartment_bill.total_bill())
        else:
            apartment_bill.change = 0

        apartment_bill.is_paid = True
        apartment_bill.save()

        messages.success(request, 'Bill paid successfully')

        send_email_task.delay(
            subject='You paid a bill',
            message=f'You have paid a bill for apartment {apartment_bill.apartment.number} for the month {month} {year} as follows: \n'
                    f'Electricity: {apartment_bill.electricity:.2f}lv \n'
                    f'Cleaning: {apartment_bill.cleaning:.2f}lv \n'
                    f'Elevator electricity: {apartment_bill.elevator_electricity:.2f}lv \n'
                    f'Elevator maintenance: {apartment_bill.elevator_maintenance:.2f}lv \n'
                    f'Entrance maintenance: {apartment_bill.entrance_maintenance:.2f}lv \n'
                    f'Total sum: {apartment_bill.total_bill():.2f}lv \n'
                    f'Change: {apartment_bill.change:.2f}lv',
            from_email='mycookbook787@gmail.com',
            recipient_list=[apartment_bill.apartment.owner.email],
        )

        return redirect(f'{reverse("manager_dashboard")}?month={month}&year={year}')
    return render(request, 'accounts/manager_dashboard.html')
