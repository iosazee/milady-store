from django.core.mail import send_mail, BadHeaderError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def send_email(subject, message, recipients):
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.EMAIL_HOST_USER

    for recipient in recipients:
        if is_valid_email(recipient):
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient],
                    fail_silently=False  # Set to True in production
                )
                print(f"Email sent successfully to {recipient}")
            except BadHeaderError:
                print("Invalid header found in the email.")
        else:
            print(f"Invalid email address: {recipient}")

# Example usage:
# subject = "Test Subject"
# message = "This is a test message."
# recipients = ["recipient1@example.com", "recipient2@example.com", "invalid_email"]

# send_email(subject, message, recipients)
