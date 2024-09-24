import os
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.context_processors import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from BuildingBillsManagement import settings
from accounts.decorators import group_required
from building.models import Apartment, ApartmentBill
from .forms import MyAccountUpdateForm
from .tasks import send_email_task
from .tokens import generate_token

User = get_user_model()


def get_building_entrance_apartments(user):
    apartment = Apartment.objects.filter(owner=user).first()
    building = apartment.building
    entrance = apartment.entrance
    apartments = Apartment.objects.filter(building=building, entrance=entrance)

    return [building, entrance, apartments]


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
            return redirect('residents')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('residents')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('residents')

        new_user = User.objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password)

        new_user.is_active = False
        new_user.save()

        from_email = settings.EMAIL_HOST_USER
        to_list = [new_user.email]
        current_site = get_current_site(request)
        email_subject = "You are invited to join Building Bills Management System"
        message = render_to_string('email_confirmation.html', {
            'name': f'{new_user.first_name} {new_user.last_name}',
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'token': generate_token.make_token(new_user)
        })
        email = EmailMessage(
            email_subject,
            message,
            settings.EMAIL_HOST_USER,
            [new_user.email],
        )
        send_mail(email_subject, message, from_email, to_list, fail_silently=True)

        messages.success(request, 'Account created successfully. Email has been sent with confirmation link')
        return redirect('residents')

    return render(request, 'accounts/residents.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        # user.profile.signup_confirmation = True
        myuser.save()
        login(request)
        messages.success(request, "Your Account has been activated!! Please reset your password to continue")
        return redirect('password_reset')
    else:
        return render(request, 'activation_failed.html')


def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        next_url = request.POST.get('next')

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
        messages.success(request, f'Welcome back {user.first_name} {user.last_name}')

        if next_url:
            return redirect(next_url)
        else:
            return redirect('dashboard')

    return render(request, 'accounts/login.html')


@login_required
def profile(request):
    form = MyAccountUpdateForm(instance=request.user)

    if request.method == 'POST':
        form = MyAccountUpdateForm(request.POST, instance=request.user)

        if User.objects.filter(email=request.POST['email']).exists() and request.user.email != request.POST['email']:
            messages.error(request, 'The Email you entered already exists')

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')

    return render(request, 'accounts/profile.html', {'form': form})


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


@login_required(redirect_field_name='next', login_url='login')
def my_bills(request):
    user = request.user
    apartment = Apartment.objects.filter(owner=user).first()

    paginator = Paginator(ApartmentBill.objects.filter(apartment__owner=user), 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'bills': page_obj,
        'apartment': apartment
    }

    return render(request, 'accounts/my_bills.html', context)


# @login_required
# @group_required('manager')
# def manager_dashboard(request):
#     now = datetime.now()
#
#     selected_month = request.GET.get('month')
#     selected_year = request.GET.get('year')
#
#     if selected_month and selected_year:
#         selected_month = int(selected_month)
#         selected_year = int(selected_year)
#     else:
#         if now.month == 1:
#             selected_month = 12
#             selected_year = now.year - 1
#         else:
#             selected_month = now.month - 1
#             selected_year = now.year
#
#     if selected_month == 0:
#         selected_month = 12
#         selected_year -= 1
#     elif selected_month == 13:
#         selected_month = 1
#         selected_year += 1
#
#     user = request.user
#     apartment = Apartment.objects.filter(owner=user).first()
#
#     if not apartment:
#         selected_month = now.month - 1
#         selected_year = now.year
#         messages.error(request, 'You have no building, entrance and apartment associated with your account')
#         return render(request, 'accounts/dashboard.html', {'month': selected_month, 'year': selected_year})
#
#     building, entrance, apartments = get_building_entrance_apartments(user)
#
#     apartment_bills = ApartmentBill.objects.filter(
#         apartment__building=building,
#         apartment__entrance=entrance,
#         for_month__month=selected_month,
#         for_month__year=selected_year
#     )
#
#     context = {
#         'entrance': entrance,
#         'apartments': apartments,
#         'bills': apartment_bills,
#         'month': selected_month,
#         'year': selected_year,
#     }
#
#     return render(request, 'accounts/manager_dashboard.html', context)


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
            return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

        given_sum = Decimal(given_sum) + apartment_bill.change

        if given_sum <= 0:
            messages.error(request, 'Sum must be greater than 0')
            return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

        if given_sum < apartment_bill.total_bill() - Decimal('0.001'):
            messages.error(request, 'Sum must be greater than or equal to total bill')
            return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

        if apartment_bill.is_paid:
            messages.error(request, 'Bill already paid')
            return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

        if given_sum >= apartment_bill.total_bill():
            apartment_bill.change = given_sum - apartment_bill.total_bill()
        else:
            apartment_bill.change = Decimal('0.0')

        apartment_bill.is_paid = True
        apartment_bill.save()

        if apartment_bill.change > 0:
            current_month_bill = ApartmentBill.objects.filter(
                apartment=apartment_bill.apartment,
                for_month__gt=apartment_bill.for_month
            ).order_by('for_month').first()

            if current_month_bill:
                current_month_bill.change += apartment_bill.change
                current_month_bill.save()

        messages.success(request, 'Bill paid successfully')

        # Prepare the context for the HTML email
        context = {
            'apartment_number': apartment_bill.apartment.number,
            'month': month,
            'year': year,
            'electricity': apartment_bill.electricity,
            'cleaning': apartment_bill.cleaning,
            'elevator_electricity': apartment_bill.elevator_electricity,
            'elevator_maintenance': apartment_bill.elevator_maintenance,
            'entrance_maintenance': apartment_bill.entrance_maintenance,
            'total': apartment_bill.total_bill(),
            'change': apartment_bill.change,
            'user': apartment_bill.apartment.owner
        }

        # Render the HTML email template
        html_email_content = render_to_string('accounts/paid_bill_email.html', context)

        # Send the email using the modified send_email_task
        send_email_task.delay(
            subject='You paid a bill',
            html_content=html_email_content,
            from_email=os.getenv('EMAIL_HOST_USER', None),
            recipient_list=[apartment_bill.apartment.owner.email],
        )

        return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

    return render(request, 'accounts/dashboard.html')


@login_required
@group_required('manager')
def residents(request):
    building = request.user.owner.filter(entrance__isnull=False).first().entrance.building
    entrance = request.user.owner.filter(entrance__isnull=False).first().entrance
    all_apartments = entrance.apartments.all()

    context = {
        'apartments': all_apartments,
        'entrance': entrance,
        'building': building
    }

    return render(request, 'accounts/residents.html', context)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'accounts/password_reset.html'
    html_email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."

    success_url = reverse_lazy('login')
