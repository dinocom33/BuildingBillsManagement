from django.contrib.auth.models import User
from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect
from django.contrib import messages


def register(request):
    if request.method == 'POST':

        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if not first_name or not last_name or not username or not email or not password or not password2:
            messages.error(request, 'All fields are required')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        new_user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email,
                                            password=password)

        new_user.save()
        messages.success(request, 'Account created successfully')
        return redirect('login')

    return render(request, 'accounts/register.html')


def login(request):
    return render(request, 'accounts/login.html')


def logout(request):
    return render(request, 'accounts/logout.html')
