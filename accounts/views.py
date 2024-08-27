from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect
from django.contrib import messages, auth

from building.models import Apartment, Bill, Entrance, ApartmentBill

User = get_user_model()


def register(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if not first_name or not last_name or not email or not password or not password2:
            messages.error(request, 'All fields are required')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        new_user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password)

        new_user.save()
        messages.success(request, 'Account created successfully')
        return redirect('login')

    return render(request, 'accounts/register.html')


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
    user = request.user
    apartment = Apartment.objects.filter(owner=user).first()
    entrance = Entrance.objects.filter(name=apartment.entrance).first()
    apartments = Apartment.objects.filter(entrance=entrance)

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

    apartment_bills = ApartmentBill.objects.filter(
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
