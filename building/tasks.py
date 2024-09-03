# tasks.py

from celery import shared_task
from django.core.mail import send_mail
from .models import ApartmentBill, Apartment


@shared_task
def create_apartment_bill_task(apartment_id, for_month, total_electricity, total_cleaning, total_elevator_electricity,
                               total_elevator_maintenance, total_entrance_maintenance, last_change, email_subject,
                               email_message, from_email, recipient_list):
    apartment = Apartment.objects.get(id=apartment_id)

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

    # Send email asynchronously
    send_mail(
        subject=email_subject,
        message=email_message,
        from_email=from_email,
        recipient_list=recipient_list,
    )

    return apartment_bill.id
