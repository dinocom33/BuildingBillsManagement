from celery import shared_task, group
from decimal import Decimal
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import ApartmentBill, Apartment


@shared_task
def create_apartment_bill_task(apartment_id, for_month, total_electricity, total_cleaning, total_elevator_electricity,
                               total_elevator_maintenance, total_entrance_maintenance, last_change, email_subject,
                               email_message, from_email, recipient_list):
    try:
        apartment = Apartment.objects.get(id=apartment_id)
    except Apartment.DoesNotExist:
        print(f"Apartment with ID {apartment_id} not found.")
        return None

    # Convert all amounts to Decimal
    total_electricity = Decimal(str(total_electricity))
    total_cleaning = Decimal(str(total_cleaning))
    total_elevator_electricity = Decimal(str(total_elevator_electricity))
    total_elevator_maintenance = Decimal(str(total_elevator_maintenance))
    total_entrance_maintenance = Decimal(str(total_entrance_maintenance))
    last_change = Decimal(str(last_change))

    # Calculate total amount and subtract last_change
    total_amount = (
        total_electricity + total_cleaning + total_elevator_electricity +
        total_elevator_maintenance + total_entrance_maintenance
    )

    if last_change > total_amount:
        last_change -= total_amount
        total_amount = Decimal('0.0')
    else:
        total_amount -= last_change

    # Create the bill
    apartment_bill = ApartmentBill.objects.create(
        apartment=apartment,
        for_month=for_month,
        electricity=total_electricity,
        cleaning=total_cleaning,
        elevator_electricity=total_elevator_electricity,
        elevator_maintenance=total_elevator_maintenance,
        entrance_maintenance=total_entrance_maintenance,
        total=total_amount,
        change=last_change if total_amount == Decimal('0.0') else Decimal('0'),  # Set initial change to 0 since we've applied last_change to total
        is_paid=False if total_amount != Decimal('0.0') else True,
    )

    # Define the context with all relevant information including last_change
    context = {
        'apartment_number': apartment.number,
        'for_month': for_month,
        'electricity': total_electricity,
        'cleaning': total_cleaning,
        'elevator_electricity': total_elevator_electricity,
        'elevator_maintenance': total_elevator_maintenance,
        'entrance_maintenance': total_entrance_maintenance,
        'previous_balance': last_change,
        'total': total_amount,
    }

    # Render the HTML and plain-text email templates
    html_email_message = render_to_string('accounts/new_bill_email.html', context)
    plain_text_message = render_to_string('accounts/new_bill_email.txt', context)

    # Create the email object
    email = EmailMultiAlternatives(
        subject=email_subject,
        body=plain_text_message,
        from_email=from_email,
        to=recipient_list,
    )

    # Attach the HTML version
    email.attach_alternative(html_email_message, "text/html")

    try:
        email.send()
    except Exception as e:
        print(f"Email sending failed: {e}")

    return apartment_bill.id


@shared_task
def create_apartment_bills_task(apartments_ids, for_month, ap_el, ap_clean, ap_elev_el, ap_maint, entr_maint,
                                email_subject_template, email_message_template, from_email):
    tasks = []
    with transaction.atomic():
        for apartment_id in apartments_ids:
            try:
                apartment = Apartment.objects.get(id=apartment_id)
            except Apartment.DoesNotExist:
                print(f"Apartment with ID {apartment_id} not found.")
                continue

            # Get the last bill and its change amount
            last_bill = ApartmentBill.objects.filter(apartment=apartment).order_by('-for_month').first()

            # Get last_change if the bill is paid (can be positive or negative)
            last_change = Decimal('0')
            if last_bill and last_bill.is_paid:
                last_change = last_bill.change
                # Set change to 0 after retrieving it
                last_bill.change = Decimal('0')
                last_bill.save()

            # Calculate individual amounts as Decimal
            electricity = Decimal(ap_el)
            cleaning = Decimal(ap_clean)
            elevator_electricity = Decimal(ap_elev_el)
            elevator_maintenance = Decimal(ap_maint)
            entrance_maintenance = Decimal(entr_maint)

            # Calculate initial total
            total_amount = (electricity + cleaning + elevator_electricity +
                            elevator_maintenance + entrance_maintenance)

            # Subtract last_change from total_amount (if negative, it will add to total)
            if last_change > total_amount:
                last_change -= total_amount
                total_amount = Decimal('0.0')
            else:
                total_amount -= last_change

            # Prepare email details
            email_subject = email_subject_template.format(apartment_number=apartment.number)
            email_message = email_message_template.format(
                apartment_number=apartment.number,
                for_month=for_month,
                electricity=electricity,
                cleaning=cleaning,
                elevator_electricity=elevator_electricity,
                elevator_maintenance=elevator_maintenance,
                entrance_maintenance=entrance_maintenance,
                previous_balance=last_change,  # Renamed to be more clear
                total=total_amount,
                change=last_change
            )
            recipient_list = [apartment.owner.email]

            tasks.append(create_apartment_bill_task.s(
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
            ))

    group(tasks).apply_async()


@shared_task
def send_message_email_task(email_subject, email_html_message, from_email, recipient_list):
    plain_text_message = strip_tags(email_html_message)

    email = EmailMultiAlternatives(
        subject=email_subject,
        body=plain_text_message,  # Plain-text version (stripped HTML)
        from_email=from_email,
        to=recipient_list,
    )

    # Attach the HTML version
    email.attach_alternative(email_html_message, "text/html")

    try:
        email.send()
    except Exception as e:
        print(f"Email sending failed: {e}")
