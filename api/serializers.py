from rest_framework import serializers
from .models import Category, Product, Review, Cart, CartItems, Order, OrderItem, Payment



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'featured',
                  'image', 'rating', 'price', 'category']

class ProductCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Product
        fields = ['title', 'description', 'featured', 'image', 'rating', 'price', 'category_id']

    def create(self, validated_data):
        category_id = validated_data.pop('category_id')
        category = Category.objects.get(pk=category_id)
        product = Product.objects.create(category=category, **validated_data)
        return product



class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "price", "image"]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(many=False)
    sub_total = serializers.SerializerMethodField(method_name="total")

    class Meta:
        model = CartItems
        fields = ["id", "cart", "product", "quantity", "sub_total"]
        ordering = ['id']

    def total(self, cartitem: CartItems):
        return cartitem.quantity * cartitem.product.price


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = CartItems
        fields = ['id', 'product_id', 'quantity']
        ordering = ['id']

        def validate_product_id(self, value):
            if not Product.objects.filter(pk=value).exists():
                raise serializers.ValidationError(
                    "There is no product associated with the given ID")

            return value

        def save(self, **kwargs):
            cart_id = self.context["cart_id"]
            product_id = self.validated_data["product_id"]
            quantity = self.validated_data["quantity"]

            try:
                cartitem = CartItems.objects.get(
                    product_id=product_id, cart_id=cart_id)
                cartitem.quantity += quantity
                cartitem.save()

                self.instance = cartitem

            except:
                self.instance = CartItems.objects.create(
                    cart_id=cart_id, **self.validated_data)

            return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField(read_only=True)
    class Meta:
        model = CartItems
        fields = ['quantity']
        ordering = ['id']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField(method_name='main_total')
    total_quantity = serializers.SerializerMethodField(
        method_name='get_total_quantity')
    # selected_items = SimpleProductSerializer()

    class Meta:
        model = Cart
        fields = ["id", "items", 'cart_total', 'total_quantity']

    def main_total(self, cart: Cart):
        items = cart.items.all()
        total = sum([item.quantity * item.product.price for item in items])
        return total

    def get_total_quantity(self, cart: Cart):
        items = cart.items.all()
        total_quantity = sum([item.quantity for item in items])
        return total_quantity


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    order = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity', 'price', 'order')

    def get_order(self, obj):
        return obj.order.id


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, read_only=True, source='product')

    class Meta:
        model = Order
        fields = ('id', 'products', 'status', 'date_created',
                  'shipping_address', 'total_cost')


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'user', 'order', 'payment_method',
                  'paymentintent_id', 'session_id', 'amount_paid', 'payment_date')