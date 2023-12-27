from django.contrib import admin
from . import models

admin.site.site_header = 'SHOPIT ADMIN DASHBOARD'
admin.site.site_title = 'ADMIN DASHBOARD'

# Register your models here.
admin.site.register(models.Category)
admin.site.register(models.Product)
admin.site.register(models.Review)
admin.site.register(models.Cart)
admin.site.register(models.CartItems)
admin.site.register(models.Order)
admin.site.register(models.OrderItem)
admin.site.register(models.Payment)