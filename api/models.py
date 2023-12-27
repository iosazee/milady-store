from django.db import models
from core.models import CustomUser
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    featured = models.BooleanField(db_index=True, default=False)
    image = models.URLField(max_length=255)
    rating = models.DecimalField(max_digits=3, decimal_places=1, db_index=True, validators=[
                                 MinValueValidator(0.5), MaxValueValidator(5)])
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='products')
    discount = models. BooleanField(default=False)
    inventory = models.IntegerField(default=5)

    def __str__(self) -> str:
        return self.title


class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews")
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(default="description")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.description


class Cart(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='shopping_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    selected_items = models.ManyToManyField(
        Product, through='CartItems', related_name='cart_products')

    def __str__(self) -> str:
        return f"{self.user}'s cart with the id of {self.id}"


class CartItems(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, blank=True, null=True, related_name='items')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, blank=True, null=True, related_name='cartitems')
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.product}  in {self.cart}"


class Order(models.Model):
    PENDING = 'pending'
    PAID = 'paid'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (PAID, 'Paid'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, related_name='crew', null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING)
    date_created = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField()
    total_cost = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Order {self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.product} ({self.quantity})"

    def get_total_price(self):
        return self.quantity * self.price


class Payment(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=50)
    paymentintent_id = models.CharField(max_length=100, blank=True, null=True)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(
        max_digits=6, decimal_places=2, db_index=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    receipt_url = models.URLField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.user}'s payment for the order {self.order.id}"
