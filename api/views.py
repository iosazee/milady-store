from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.pagination import PageNumberPagination
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions, generics, views
from rest_framework import status
from rest_framework.decorators import action
import requests
from django.utils.decorators import method_decorator
from django.middleware.csrf import rotate_token
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from rest_framework_simplejwt.tokens import  OutstandingToken, BlacklistedToken
from .models import Cart, Category, Order, OrderItem, Product, Review, CartItems, Payment
from .serializers import OrderItemSerializer, OrderSerializer, CategorySerializer, ProductSerializer, ReviewSerializer, CartSerializer, CartItemSerializer, AddCartItemSerializer, UpdateCartItemSerializer, PaymentSerializer, ProductCreateSerializer
from core.serializers import UserCreateSerializer
from .permissions import IsReviewOwner
from rest_framework_nested import routers
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from core.models import CustomUser
from . import views
from datetime import datetime
from django.utils.timezone import make_aware
import stripe
from decimal import Decimal
from django.template import Context, Template
from django.core.mail import EmailMessage


FRONTEND_DOMAIN = 'https://eeki.shop'
stripe.api_key = settings.STRIPE_SECRET_KEY

class IndexView(View):
    def get(self, request, *args, **kwargs):
        router = routers.DefaultRouter()
        # router.register('user', views.UserViewSet, basename='user')
        router.register('categories', views.CategoryViewSet, basename='categories')
        router.register('products', views.ProductViewset, basename='products')
        router.register('cart', views.CartViewSet, basename='carts')
        router.register('order-items', views.OrderItemViewSet, basename='order-items')


        # Nested review view: nested in the product view
        review_router = routers.NestedSimpleRouter(
            router, r'products', lookup='product')
        review_router.register(r'reviews', views.ReviewViewSet, basename='product-reviews')

        # Nested cartitem view: nested in the cart view
        cartitem_router = routers.NestedSimpleRouter(router, r'cart', lookup='cart')
        cartitem_router.register(r'items', views.CartItemViewSet, basename='cart-items')

        endpoints = {
            # 'user-list': reverse('user-list'),
            # 'user-detail': reverse('user-detail', args=[1]),
            'categories-list': reverse('categories-list'),
            'categories-detail': reverse('categories-detail', args=[1]),
            'products-list': reverse('products-list'),
            'products-detail': reverse('products-detail', args=[1]),
            'carts-list': reverse('carts-list'),
            'carts-detail': reverse('carts-detail', args=[1]),
            'order-items-list': reverse('order-items-list'),
            'order-items-detail': reverse('order-items-detail', args=[1]),
            'product-reviews-list': reverse('product-reviews-list', args=[1]),
            'cart-items-list': reverse('cart-items-list', args=[1]),
            'order-create': reverse('order-create'),
            'order-detail': reverse('order-detail', args=[1]),
            'group-manager-list': reverse('group-manager'),
            'group-manager-create': reverse('group-manager'),
            'group-manager-destroy': reverse('group-manager'),
            'delivery-crew-list': reverse('delivery-crew'),
            'delivery-crew-create': reverse('delivery-crew'),
            'delivery-crew-destroy': reverse('delivery-crew'),
        }

        links = [{'name': name, 'url': url} for name, url in endpoints.items()]

        return JsonResponse({'endpoints': links})


def confirm_email(request, user_id, token):
    try:
        user = get_user_model().objects.get(pk=user_id)
        if user.confirmation_token == token:
            user.email_confirmed = True
            user.save()
            return JsonResponse({'status': 'success', 'message': 'Email confirmed successfully'})
    except get_user_model().DoesNotExist:
        pass

    return JsonResponse({'status': 'error', 'message': 'Invalid confirmation link'})




@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user:
        login(request, user)

        # Get user ID from the authenticated user
        user_id = user.id if user else None

        authorization_header = request.headers.get('Authorization', '')
        if authorization_header.startswith('JWT '):
            access_token = authorization_header[len('JWT '):]
            if access_token:
                request.session['access_token'] = access_token

        # Make a request to the 'jwt-create' endpoint to obtain the refresh token
        token_create_url = 'http://127.0.0.1:8000/auth/jwt/create'
        token_create_data = {'email': email, 'password': password}
        token_create_response = requests.post(token_create_url, data=token_create_data)

        if token_create_response.status_code == status.HTTP_200_OK:
            token_data = token_create_response.json()
            refresh_token = token_data.get('refresh', '')

            if refresh_token:
                # Store the refresh token in the cache
                user_id = str(user.id)
                cache_key = f'refresh_token_{user_id}'
                cache.set(cache_key, refresh_token, timeout=604800)
                cache.touch(cache_key, timeout=604800)

        response_data = {'detail': 'Login successful', 'response_data': request.data,
            'user_id': user_id}

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)




@api_view(['POST'])
# @permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Check if the user is logged in
        if request.user.is_authenticated:
            # Log out the user
            logout(request)

            # Clear the user's session data
            session_key = request.session.session_key
            if session_key:
                Session.objects.filter(session_key=session_key).delete()

            # Rotate CSRF token
            rotate_token(request)

            return JsonResponse({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'detail': 'User is not logged in'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return JsonResponse({'detail': f'Error during logout: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer


class ProductPagination(PageNumberPagination):
    page_size = 10

class ProductViewset(viewsets.ModelViewSet):
    queryset = Product.objects.order_by('id')
    ordering_fields = ['category', 'price']
    search_fields = ['title', 'category__title']
    pagination_class = ProductPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer

    def get_permissions(self):
        permission_classes = [permissions.AllowAny]

        if self.request.method != 'GET':
            permission_classes.append(permissions.IsAdminUser)

        return [permission() for permission in permission_classes]

    @method_decorator(cache_page(60 * 30))  # Cache the response for 30 minutes
    def list(self, request, *args, **kwargs):
        # Attempt to retrieve cached data
        cached_data = cache.get('product_list')

        if cached_data is not None:
            # Return cached data
            return Response(cached_data)

        # Get the fully processed response from the super().list method
        response = super().list(request, *args, **kwargs)

        if settings.MY_PROTOCOL == "https":
            if response.data["next"]:
                response.data["next"] = response.data["next"].replace(
                "http://", "https://"
            )
            if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace(
                "http://", "https://"
            )

        # Create a new Response object with the data
        new_response = Response(response.data)

        # Set accepted_renderer to JSONRenderer instance
        new_response.accepted_renderer = JSONRenderer()

        # Set accepted_media_type to JSONRenderer media type
        new_response.accepted_media_type = JSONRenderer.media_type

        # Set renderer_context to a dictionary
        new_response.renderer_context = {'view': self}

        # Manually render the response content
        new_response.render()

        # Store the fully rendered response content in the cache for 30 minutes
        cache.set('product_list', new_response.data, 60 * 30)

        return new_response

# def replace_url(url):
#      return url.replace("http://", "https://")


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    @action(detail=True, methods=['get'])
    def product_reviews(self, request, pk=None):
        """
        Get all reviews for a specific product.
        """
        product = Product.objects.get(pk=pk)
        reviews = product.reviews.all()
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        """
        Set different permissions for different actions.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsReviewOwner]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Set the user of the review to the current user.
        """
        serializer.save(user=self.request.user)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    authentication_classes = (JWTAuthentication,)

    def create(self, request, *args, **kwargs):
        # Get the user from the request
        user = request.user

        # Check if the user already has a cart
        cart = Cart.objects.filter(user=user).first()
        if cart:
            if cart.completed:
                cart.completed = False
                cart.save()
            serializer = self.get_serializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # If the user does not have a cart, create a new one
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the cart with the user information
        cart = serializer.save(user=user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CartItemViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart_id = self.kwargs.get("cart_pk")
        if cart_id is None:
            return CartItems.objects.none()
        return CartItems.objects.filter(cart_id=cart_id).order_by('id')

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs.get("cart_pk")}

    def perform_create(self, serializer):
        cart_id = self.kwargs.get("cart_pk") or self.request.session.get("cart_id")
        if cart_id is None:
            return Response(
                {"error": "cart_id must be specified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.request.session["cart_id"] = cart_id
        try:
            cart = get_object_or_404(Cart, pk=cart_id)
        except ValidationError:
            return Response(
                {"error": "Invalid cart_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        product_id = data.get("product_id")
        product = get_object_or_404(Product, pk=product_id)
        quantity = data.get("quantity", 1)
        cart_item = CartItems.objects.filter(
            cart=cart, product=product).first()
        if cart_item:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            cart_item = serializer.save(
                cart=cart, product=product, quantity=quantity)

    def perform_destroy(self, instance):
        if instance.quantity > 1:
            instance.quantity -= 1
            instance.save()
        else:
            instance.delete()

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return OrderItem.objects.all().order_by('id')
        else:
            order_items = OrderItem.objects.filter(
                order__user=self.request.user).order_by('id')
            order_ids = order_items.values_list('order', flat=True).distinct()
            orders = Order.objects.filter(id__in=order_ids)
            return order_items.filter(order__in=orders)



class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        elif self.request.user.groups.count() == 0:
            return Order.objects.filter(cart__user=self.request.user)
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(status=Order.PENDING, cart__items__product__seller=self.request.user)
        else:
            return Order.objects.all()

    def create(self, request, *args, **kwargs):
        user_id = request.data.get('user_id', None)
        user = get_object_or_404(CustomUser, id=user_id)
        if user_id is None:
            return Response({'message': 'user_id is required to create an order'}, status=status.HTTP_400_BAD_REQUEST)

        cart_items = CartItems.objects.filter(cart__user_id=user_id)
        if not cart_items.exists():
            return Response({'message': 'no items in cart'})

        order = Order(cart=cart_items.first().cart,
                      total_cost=self.get_total_price(cart_items), user=user)
        order.save()

        for cart_item in cart_items:
            OrderItem.objects.create(order=order, product=cart_item.product,
                                     quantity=cart_item.quantity, price=cart_item.product.price)

        cart_items.delete()

        serialized_order = OrderSerializer(order)
        return Response(serialized_order.data)

    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        order.shipping_address = request.data['shipping_address']
        order.save()
        serialized_order = OrderSerializer(order)
        return Response(serialized_order.data)

    def get_total_price(self, cart_items):
        return sum([cart_item.quantity * cart_item.product.price for cart_item in cart_items])



class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        order = self.get_object()

        # check if the user who made the request is the owner of the order or an admin user
        if request.user == order.cart.user or request.user.is_staff:
            serializer = self.serializer_class(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'You do not have permission to access this order.'}, status=status.HTTP_403_FORBIDDEN)



class PaymentWithStripeView(APIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Retrieve the order object for the user
        order_id = request.data.get('order_id')
        shipping_address = request.data.get('shipping_address', '')
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order does not exist or is not owned by the user.'}, status=status.HTTP_400_BAD_REQUEST)
        # Update the shipping_address
        order.shipping_address = shipping_address
        order.save()
        # Fetch order items associated with the order
        order_items = OrderItem.objects.filter(order=order)

        # Check if the order has already been paid for
        if Payment.objects.filter(Q(order=order) & Q(user=request.user)).exists():
            return JsonResponse({'error': 'Order has already been paid for.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the total cost based on order items
        total_cost = sum([item.quantity * item.price for item in order_items])

        # Extract product names and images from order items
        product_names = [item.product.title for item in order_items]
        product_images = [item.product.image for item in order_items]

        # Create line_items dynamically
        line_items = [
            {
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {
                        'name': product_name,
                        'images': [product_image],
                    },
                    'unit_amount': int(item.price * 100),  # Convert to pennies
                },
                'quantity': item.quantity,
            }
            for item, product_name, product_image in zip(order_items, product_names, product_images)
        ]

        # Create a Stripe Checkout Session
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                metadata={'order_id': order.id},
                mode='payment',
                success_url=FRONTEND_DOMAIN + '/payment/confirm/' + '?success=true',
                cancel_url=FRONTEND_DOMAIN + '/payment/cancel/' + '?canceled=true',
            )

            # Return both session_id and session.url to the frontend
            return JsonResponse({'session_id': session.id, 'session_url': session.url})
        except Exception as e:
            return Response({'msg': 'something went wrong while creating stripe session', 'error': str(e)}, status=500)




@csrf_exempt
def stripe_webhook_view(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':

        # threading.Thread(target=send_success, args=[request]).start()
        response = StreamingHttpResponse(status=200)
        response.streaming_content = ["ok"]

        session = stripe.checkout.Session.retrieve(
            event['data']['object']['id'],
            expand=['customer', 'payment_intent.latest_charge']
        )

        # Check if payment is successful
        if session and session.payment_status == 'paid':
            # Retrieve the order ID from the session metadata
            order_id = session.metadata.get('order_id')
            # Retrieve the order object
            order = Order.objects.get(id=order_id)
            # Update the order status to 'paid'
            order.status = 'paid'
            order.save()

            # Convert amount_total to pounds (or the relevant currency)
            amount_total_in_pounds = Decimal(session.amount_total) / 100
            receipt_url = session.payment_intent.latest_charge.get('receipt_url')
            # Update the Payment model with the payment details
            payment_date = make_aware(datetime.utcfromtimestamp(session.created))
            payment = Payment(
                user=order.user,
                order=order,
                paymentintent_id=session.payment_intent.id,
                session_id=session.id,
                amount_paid=amount_total_in_pounds,
                payment_date=payment_date,
                receipt_url=receipt_url,
            )
            payment.save()
            # Send an email to the user with the payment details
            print(f'receipt url: {receipt_url}')
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
    # Passed signature verification
    return HttpResponse(status=200)



# def send_success(request):
#     return HttpResponse(status=200)



class GroupViewset(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def list(self, request):
        users = CustomUser.objects.all().filter(groups__name='Manager')
        serialized_users = UserCreateSerializer(users, many=True)
        return Response(serialized_users.data)

    def create(self, request):
        user = get_object_or_404(CustomUser, email=request.data['email'])
        managers = Group.objects.get(name='Manager')
        managers.user_set.add(user)
        return Response({'message': 'user added to the managers group'}, status.HTTP_202_ACCEPTED)

    def destroy(self, request):
        user = get_object_or_404(CustomUser, email=request.data['email'])
        managers = Group.objects.get(name='Manager')
        managers.user_set.remove(user)
        return Response({'message': "user removed from managers' group"}, status.HTTP_200_OK)



class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    # throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def list(self, request):
        users = CustomUser.objects.all().filter(groups__name='Delivery Crew')
        serialized_users = UserCreateSerializer(users, many=True)
        return Response(serialized_users.data)

    def create(self, request):
        if self.request.user.is_superuser == False:
            if self.request.user.groups.filter(name='Manager').exists() == False:
                return Response({'message': 'forbidden'}, status.HTTP_403_FORBIDDEN)

        user = get_object_or_404(CustomUser, email=request.data['email'])
        delivery_crew = Group.objects.get(name='Delivery Crew')
        delivery_crew.user_set.add(user)
        return Response({'message': 'user added to the delivery crew group'}, status.HTTP_202_ACCEPTED)


    def destroy(self, request):
        # setting up conditions only for admin and superusers to be able to use this method
        if self.request.user.is_superuser == False:
            if self.request.user.groups.filter(name='Manager').exists() == False:
                return Response({'message': 'forbidden'}, status.HTTP_403_FORBIDDEN)

