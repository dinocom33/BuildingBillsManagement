from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

@shared_task
def send_email_task(subject, html_content, from_email, recipient_list):
    plain_text_content = strip_tags(html_content)

    # Create email object with plain-text body as fallback
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_text_content,
        from_email=from_email,
        to=recipient_list,
    )

    # Attach the HTML version
    email.attach_alternative(html_content, "text/html")

    try:
        email.send()
    except Exception as e:
        print(f"Error sending email: {e}")
