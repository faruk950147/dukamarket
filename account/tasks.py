from django.core.mail import EmailMessage
from django.conf import settings
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_email_web(self, email, otp):
    try:
        domain = "127.0.0.1:8000"
        scheme = "http"
        path = "account/verify-otp/"
        subject = "OTP Verification"
        message = f"Your OTP is {otp}. It will expire in 5 minutes.\n{scheme}://{domain}/{path}"
        
        email_obj = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        email_obj.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)
    

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_otp_email_api(self, email, otp):
    try:
        domain = "127.0.0.1:8000"
        scheme = "http"
        path = "api/account/verify-otp/"
        subject = "OTP Verification"
        message = f"Your OTP is {otp}. It will expire in 5 minutes.\n{scheme}://{domain}/{path}"
        
        email_obj = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email]
        )
        email_obj.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc)