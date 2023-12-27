# Generated by Django 5.0 on 2023-12-23 15:22

from django.db import migrations, models

def set_default_values(apps, schema_editor):
    CustomUser = apps.get_model('core', 'CustomUser')

    # Set default values for CustomUser model
    for user in CustomUser.objects.all():
        if user.address is None:
            user.address = 'Some Default Address, in some default city.'
        if user.postal_code is None:
            user.postal_code = 'Default Postal Code'
        if user.phone_number is None:
            user.phone_number = '0900000122000'
        if user.sex is None:
            user.sex = 'M'
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_customuser_confirmation_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='sex',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.RunPython(set_default_values),
    ]
