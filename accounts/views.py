from calendar import month
from datetime import datetime
from lib2to3.fixes.fix_input import context

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect
from django.contrib import messages, auth

from building.models import Apartment, Bill, Entrance

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
    apartment = Apartment.objects.all().order_by('number')
    bill = Bill.objects.filter(for_month=datetime.now()).order_by('apartment__number')
    entrance = user.entrance
    month = datetime.now().strftime('%B %Y')

    context = {
        'bills': bill,
        'month': month,
        'entrance': entrance,
    }

    return render(request, 'accounts/dashboard.html', context)