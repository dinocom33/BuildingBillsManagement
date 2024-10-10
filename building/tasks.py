import logging

from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import ApartmentBill, Apartment


@shared_task
def create_apartment_bill_task(apartment_id, for_month, total_electricity, total_cleaning, total_elevator_electricity,
                               total_elevator_maintenance, total_entrance_maintenance, last_change, email_subject,
                               email_message, from_email, recipient_list):
    apartment = Apartment.objects.get(id=apartment_id)

    # Create the bill
    apartment_bill = ApartmentBill.objects.create(
        apartment=apartment,
        for_month=for_month,
        change=last_change,
        electricity=float(total_electricity),
        cleaning=float(total_cleaning),
        elevator_electricity=float(total_elevator_electricity),
        elevator_maintenance=float(total_elevator_maintenance),
        entrance_maintenance=float(total_entrance_maintenance),
    )

    # Define the context to be passed to the HTML template
    context = {
        'apartment_number': apartment.number,
        'for_month': for_month,
        'electricity': total_electricity,
        'cleaning': total_cleaning,
        'elevator_electricity': total_elevator_electricity,
        'elevator_maintenance': total_elevator_maintenance,
        'entrance_maintenance': total_entrance_maintenance,
        'total': total_electricity + total_cleaning + total_elevator_electricity + total_elevator_maintenance + total_entrance_maintenance,
    }

    # Render the HTML template with context
    html_email_message = render_to_string('accounts/new_bill_email.html', context)

    # Create the email object
    email = EmailMultiAlternatives(
        subject=email_subject,
        body=email_message,  # Fallback plain text version
        from_email=from_email,
        to=recipient_list,
    )

    # Attach the HTML version
    email.attach_alternative(html_email_message, "text/html")

    # Send the email
    email.send()

    return apartment_bill.id


@shared_task
def create_apartment_bills_task(apartments_ids, for_month, ap_el, ap_clean, ap_elev_el, ap_maint, entr_maint,
                                email_subject_template, email_message_template, from_email):
    with transaction.atomic():
        for apartment_id in apartments_ids:
            apartment = Apartment.objects.get(id=apartment_id)
            last_bill = ApartmentBill.objects.filter(apartment=apartment).order_by('-for_month').first()

            if last_bill is None:
                last_change = 0
            else:
                if last_bill.is_paid:
                    last_change = last_bill.change
                    last_bill.change = 0
                    last_bill.save()

            # Calculate individual amounts
            electricity = ap_el
            cleaning = ap_clean
            elevator_electricity = ap_elev_el
            elevator_maintenance = ap_maint
            entrance_maintenance = entr_maint

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
                total=(electricity + cleaning + elevator_electricity + elevator_maintenance + entrance_maintenance)
            )
            recipient_list = [apartment.owner.email]

            # Call the existing task to create apartment bill and send email
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


@shared_task
def send_message_email_task(email_subject, email_html_message, from_email, recipient_list):
    email = EmailMultiAlternatives(
        subject=email_subject,
        body=strip_tags(email_html_message),  # Plain-text version (stripped HTML)
        from_email=from_email,
        to=recipient_list,
    )

    # Attach the HTML version
    email.attach_alternative(email_html_message, "text/html")

    email.send()

