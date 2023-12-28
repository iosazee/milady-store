from django.template import Context, Template
from django.core.mail import EmailMessage
from django.dispatch import receiver
from djoser.signals import user_registered
from django.conf import settings
from django.db.models.signals import Signal, post_save
from urllib.parse import urlunparse
from .models import Payment


html_content_template = Template("""
<html>
    <head>
        <link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css'>
    </head>
    <body class='container' style='font-family: Arial, sans-serif; color: #333;'>
        <img src='https://res.cloudinary.com/dj7gm1w72/image/upload/v1703311634/logo_fixtgx.png' alt='Shopit logo' class='img-fluid'>
        <p class='lead mb-4'>Welcome to Shopit Dear {{ user.last_name }}.</p>
        <p class='lead mb-4'>We are happy to have you onboard.</p>
       <p class='lead mb-4'>Kindly confirm your email by
        <a href='{{ confirmation_url }}' class='text-primary font-weight-bold'>clicking here</a> to enjoy our services.
        </p>
        <div>
            <img src='https://res.cloudinary.com/dj7gm1w72/image/upload/v1703323936/favicon_jig0fp.ico' alt='Logo' class='img-fluid' width='50'>
            <p><small>ShopIT, your one-stop total shopping experience!</small></p>
        </div>
    </body>
</html>
""")



@receiver(user_registered)
def send_welcome_email(sender, request, user, **kwargs):
    frontend_domain = 'eeki.shop'
    confirmation_path = f'/email/confirm/{user.id}/{user.confirmation_token}/'
    confirmation_url = urlunparse(('https', frontend_domain, confirmation_path, '', '', ''))

    subject = f"Welcome to ShopIT, {user.last_name}"

    context = Context({'user': user, 'confirmation_url': confirmation_url})
    html_content = html_content_template.render(context)

    message = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.content_subtype = 'html'
    message.send()




