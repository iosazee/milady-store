# from django.template.loader import Context, Template
# from django.core.mail import EmailMessage
# from django.conf import settings
# from .models import Payment

# from django.db import migrations, models

# def set_default_values(apps, schema_editor):
#     CustomUser = apps.get_model('your_app_name', 'CustomUser')
    
#     # Set default values for CustomUser model
#     for user in CustomUser.objects.all():
#         if user.address is None:
#             user.address = 'Default Address'
#         if user.postal_code is None:
#             user.postal_code = 'Default Postal Code'
#         if user.phone_number is None:
#             user.phone_number = 'Default Phone Number'
#         if user.sex is None:
#             user.sex = 'Default Sex'
#         user.save()

#     # Set default values for Payment model
#     # for payment in Payment.objects.all():
#     #     if payment.receipt_url is None:
#     #         payment.receipt_url = 'Default Receipt URL'
#     #     payment.save()

# class Migration(migrations.Migration):

#     dependencies = [
#         # Add your existing dependencies here
#     ]

#     operations = [
#         migrations.RunPython(set_default_values),
#     ]






















