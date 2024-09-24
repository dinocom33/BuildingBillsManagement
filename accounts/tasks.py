from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

@shared_task
def send_email_task(subject, html_content, from_email, recipient_list):
    # Create email object
    email = EmailMultiAlternatives(subject, '', from_email, recipient_list)
    email.attach_alternative(html_content, "text/html")
    email.send()
