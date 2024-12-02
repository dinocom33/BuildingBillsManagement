import os
from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView, PasswordChangeView
from django.contrib.messages.context_processors import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages, auth
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic import UpdateView, TemplateView, ListView

from BuildingBillsManagement import settings
from accounts.decorators import group_required
from building.models import Apartment, ApartmentBill, TotalMaintenanceAmount, Building, Entrance
from ensure_celery_running import ensure_celery_running
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


@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('manager'), name='dispatch')  # Replace `group_required` decorator with your actual implementation
class RegisterView(View):
    template_name = 'accounts/residents.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        building_number = request.POST.get('building')
        entrance_name = request.POST.get('entrance')
        floor = request.POST.get('floor')
        apartment_number = request.POST.get('apartment')

        if not first_name or not last_name or not email:
            messages.error(request, 'All fields are required')
            return redirect('residents')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('residents')

        # Generate a random password
        password = get_random_string(length=12)

        # Create new user
        new_user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        new_user.is_active = False
        new_user.save()

        # Handle building and apartment relationships
        building, _ = Building.objects.get_or_create(number=building_number)
        entrance, _ = Entrance.objects.get_or_create(name=entrance_name, building_id=building.id)

        if Apartment.objects.filter(building_id=building.id, entrance_id=entrance.id, floor=floor, number=apartment_number).exists():
            messages.error(request, 'Apartment already exists')
            return redirect('residents')

        Apartment.objects.create(
            building_id=building.id,
            entrance_id=entrance.id,
            floor=floor,
            number=apartment_number,
            owner=new_user
        )

        # Send confirmation email
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
        send_mail(email_subject, message, settings.EMAIL_HOST_USER, [new_user.email], fail_silently=True)

        messages.success(request, 'Account created successfully. Email has been sent with a confirmation link')
        return redirect('residents')


class ActivateAccountView(View):
    template_name_failure = 'activation_failed.html'

    def get(self, request, uidb64, token):
        try:
            # Decode the user ID and fetch the user
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        # Verify the token and activate the account if valid
        if user is not None and generate_token.check_token(user, token):
            self.activate_user(user, request)
            return redirect('password_reset')

        # Render the failure template if activation fails
        return render(request, self.template_name_failure)

    def activate_user(self, user, request):
        """Activate the user account and log them in."""
        user.is_active = True
        user.save()
        # login(request, user)
        messages.success(request, "Your Account has been activated! Please reset your password to continue.")


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        # Redirect authenticated users to the dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        # Handle login form submission
        if request.user.is_authenticated:
            return redirect('dashboard')

        email = request.POST.get('email')
        password = request.POST.get('password')
        next_url = request.POST.get('next')

        if not email or not password:
            messages.error(request, 'All fields are required')
            return redirect('login')

        # Authenticate the user
        user = authenticate(request, email=email, password=password)
        if user is None:
            messages.error(request, 'Wrong username or password')
            return redirect('login')

        # Log the user in
        login(request, user)  # Use the correct import
        messages.success(request, f'Welcome {user.first_name} {user.last_name}')

        # Redirect to the next URL or dashboard
        return redirect(next_url) if next_url else redirect('dashboard')


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = MyAccountUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        # Return the currently logged-in user
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the password change form to the context
        if 'password_form' not in kwargs:
            context['password_form'] = PasswordChangeForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'old_password' in request.POST:
            # Handle password change form submission
            password_form = PasswordChangeForm(user=self.request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Your password has been updated successfully.')
                return redirect(self.success_url)
            else:
                messages.error(request, 'Please correct the errors below.')
                return self.render_to_response(self.get_context_data(password_form=password_form))
        return super().post(request, *args, **kwargs)



@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, 'Logout successful')
        return redirect('login')


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = datetime.now()

        # Retrieve selected month and year from query parameters
        selected_month = self.request.GET.get('month')
        selected_year = self.request.GET.get('year')

        if selected_month and selected_year:
            selected_month = int(selected_month)
            selected_year = int(selected_year)
        else:
            # Default to the previous month
            if now.month == 1:
                selected_month = 12
                selected_year = now.year - 1
            else:
                selected_month = now.month - 1
                selected_year = now.year

        # Adjust edge cases for months
        if selected_month == 0:
            selected_month = 12
            selected_year -= 1
        elif selected_month == 13:
            selected_month = 1
            selected_year += 1

        # Fetch the logged-in user
        user = self.request.user
        apartment = Apartment.objects.filter(owner=user).first()

        # Handle users with no associated apartment
        if not apartment:
            selected_month = now.month - 1
            selected_year = now.year
            messages.error(self.request, 'You have no building, entrance, and apartment associated with your account')
            context.update({
                'month': selected_month,
                'year': selected_year,
            })
            return context

        # Retrieve building, entrance, and apartments
        building = apartment.building
        entrance = apartment.entrance
        apartments = Apartment.objects.filter(building=building, entrance=entrance)

        # Fetch bills for the selected month and year
        apartment_bills = ApartmentBill.objects.filter(
            apartment__building=building,
            apartment__entrance=entrance,
            for_month__month=selected_month,
            for_month__year=selected_year
        )

        # Populate context
        context.update({
            'entrance': entrance,
            'apartments': apartments,
            'bills': apartment_bills,
            'month': selected_month,
            'year': selected_year,
        })
        return context


class MyBillsView(LoginRequiredMixin, ListView):
    model = ApartmentBill
    template_name = 'accounts/my_bills.html'
    context_object_name = 'bills'
    paginate_by = 10
    login_url = 'login'
    redirect_field_name = 'next'

    def get_queryset(self):
        """
        Return bills filtered by the current user's apartment.
        """
        user = self.request.user
        return ApartmentBill.objects.filter(apartment__owner=user)

    def get_context_data(self, **kwargs):
        """
        Add the user's apartment to the context.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['apartment'] = get_object_or_404(Apartment, owner=user)
        return context


@method_decorator([login_required, group_required('manager'), ensure_celery_running], name='dispatch')
class PayBillView(View):
    template_name = 'accounts/dashboard.html'

    def post(self, request, bill_id):
        # Fetch the apartment bill
        apartment_bill = get_object_or_404(ApartmentBill, id=bill_id)
        given_sum = request.POST.get('sum')
        month = request.POST.get('month', '')
        year = request.POST.get('year', '')
        total_maintenance_amount = TotalMaintenanceAmount.objects.filter(
            building__entrance=apartment_bill.apartment.entrance
        ).first()

        # Validate given sum
        if not given_sum:
            return self._handle_error('Sum is required', month, year)

        given_sum = Decimal(given_sum) + apartment_bill.change

        if given_sum <= 0:
            return self._handle_error('Sum must be greater than 0', month, year)

        if given_sum < apartment_bill.total_bill() - Decimal('0.001'):
            return self._handle_error('Sum must be greater than or equal to total bill', month, year)

        if apartment_bill.is_paid:
            return self._handle_error('Bill already paid', month, year)

        # Process the bill payment
        self._process_payment(apartment_bill, given_sum, total_maintenance_amount)

        # Send confirmation email
        self._send_confirmation_email(apartment_bill, month, year)

        # Redirect to dashboard with success message
        messages.success(request, 'Bill paid successfully')
        return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

    def get(self, request, *args, **kwargs):
        # Redirect to the dashboard if accessed via GET
        return render(request, self.template_name)

    def _handle_error(self, error_message, month, year):
        """Handle validation errors by showing a message and redirecting."""
        messages.error(self.request, error_message)
        return redirect(f'{reverse("dashboard")}?month={month}&year={year}')

    def _process_payment(self, apartment_bill, given_sum, total_maintenance_amount):
        """Process the bill payment and update relevant records."""
        if given_sum >= apartment_bill.total_bill():
            apartment_bill.change = given_sum - apartment_bill.total_bill()
        else:
            apartment_bill.change = Decimal('0.0')

        apartment_bill.is_paid = True
        apartment_bill.save()

        # Apply change to the next month's bill if applicable
        if apartment_bill.change > 0:
            next_month_bill = ApartmentBill.objects.filter(
                apartment=apartment_bill.apartment,
                for_month__gt=apartment_bill.for_month
            ).order_by('for_month').first()

            if next_month_bill:
                next_month_bill.change += apartment_bill.change
                apartment_bill.change = Decimal('0.0')
                apartment_bill.save()
                next_month_bill.save()

        # Update the total maintenance amount
        if total_maintenance_amount:
            total_maintenance_amount.amount += apartment_bill.entrance_maintenance
            total_maintenance_amount.save()

    def _send_confirmation_email(self, apartment_bill, month, year):
        """Prepare and send a confirmation email."""
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

        html_email_content = render_to_string('accounts/paid_bill_email.html', context)

        send_email_task.delay(
            subject='You paid a bill',
            html_content=html_email_content,
            from_email=os.getenv('EMAIL_HOST_USER', None),
            recipient_list=[apartment_bill.apartment.owner.email],
        )


@method_decorator([login_required, group_required('manager')], name='dispatch')
class ResidentsView(TemplateView):
    template_name = 'accounts/residents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Fetch user data
            owner = self._get_owner_with_entrance()

            if owner and owner.entrance:
                # Owner with an entrance
                entrance = owner.entrance
                building = entrance.building
                all_apartments = entrance.apartments.all()
                floor = all_apartments.first().floor if all_apartments.exists() else None
            else:
                # No owner or entrance, fetch apartments created by user
                all_apartments, building, entrance, floor = self._get_apartments_without_owner()

            context.update({
                'apartments': all_apartments,
                'entrance': entrance,
                'building': building,
                'floor': floor,
                'no_data': len(all_apartments) == 0
            })

            # Add a message if no apartments are found
            if len(all_apartments) == 0:
                messages.info(self.request, 'No residents found.')

        except Exception as e:
            # Handle any unexpected errors
            messages.error(self.request, f'An error occurred: {str(e)}')
            context.update({
                'apartments': [],
                'entrance': None,
                'building': None,
                'error': str(e)
            })

        return context

    def _get_owner_with_entrance(self):
        """Fetch the owner's entrance and related data."""
        return (
            self.request.user.owner
            .select_related('entrance__building')
            .prefetch_related('entrance__apartments')
            .filter(entrance__isnull=False)
            .first()
        )

    def _get_apartments_without_owner(self):
        """Fetch apartments when the user does not have an associated entrance."""
        all_apartments = Apartment.objects.filter(
            building__entrance__apartments__isnull=False
        ).select_related(
            'building',
            'entrance'
        ).distinct()

        if all_apartments.exists():
            first_apartment = all_apartments.first()
            building = first_apartment.building
            entrance = first_apartment.entrance
            floor = first_apartment.floor
        else:
            building = None
            entrance = None
            floor = None

        return all_apartments, building, entrance, floor


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'accounts/password_reset.html'
    html_email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."

    success_url = reverse_lazy('login')
