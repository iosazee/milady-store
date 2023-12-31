from django.core.mail import send_mail, BadHeaderError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template import Context, Template
from django.core.mail import EmailMessage

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


def send_payment_confirmation_email(order, receipt_url):
    html_content_template = Template("""
        <html>
            <head>
                <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css'>
            </head>
            <body class='container' style='font-family: Arial, sans-serif; color: #333;'>
                <img src='https://res.cloudinary.com/dj7gm1w72/image/upload/v1703311634/logo_fixtgx.png' alt='Shopit logo' class='img-fluid'>
                <p class='lead mb-4'>Thank you for your order {{ order.user.last_name }}. Your order with ID {{ order.id }} has been successfully paid.</p>
                <p class='lead mb-4'>
                    We will process your order shortly, and you can view and download your receipt by   <a href='{{ receipt_url }}' class='text-primary font-weight-bold'>clicking here</a>
                </p>
                <div>
                    <img src='https://res.cloudinary.com/dj7gm1w72/image/upload/v1703323936/favicon_jig0fp.ico' alt='Logo' class='img-fluid' width='50'>
                    <p><small>ShopIT, your one-stop total shopping experience!</small></p>
                </div>
            </body>
        </html>
        """)

    subject = f"Payment Confirmation - Order #{order.id}"

    context = Context({'order': order,  'receipt_url': receipt_url})
    html_content = html_content_template.render(context)

    message = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )
    message.content_subtype = 'html'
    message.send()
