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


@shared_task
def create_apartment_bills_task(apartments_ids, for_month, ap_el, ap_clean, ap_elev_el, ap_maint, entr_maint, email_subject_template, email_message_template, from_email):
    for apartment_id in apartments_ids:
        apartment = Apartment.objects.get(id=apartment_id)
        last_bill = ApartmentBill.objects.filter(apartment=apartment).last()

        if last_bill is None:
            last_change = 0
        else:
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
