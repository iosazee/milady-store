from django.urls import path, include
from . import views
from rest_framework_nested import routers
from django.views.decorators.csrf import csrf_exempt

router = routers.DefaultRouter()

router.register('categories', views.CategoryViewSet, basename='categories')
router.register('products', views.ProductViewset, basename='products')
router.register('cart', views.CartViewSet, basename='carts')
router.register('order-items', views.OrderItemViewSet, basename='order-items')


# nested review view: nested in the product view
review_router = routers.NestedSimpleRouter(
    router, r'products', lookup='product')
review_router.register(r'reviews', views.ReviewViewSet,
                       basename='product-reviews')


# nested cartitem view: nested in the cart view
cartitem_router = routers.NestedSimpleRouter(router, r'cart', lookup='cart')
cartitem_router.register(
    r'items', views.CartItemViewSet, basename='cart-items')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(review_router.urls)),
    path('', include(cartitem_router.urls)),
    path('orders/', views.OrderView.as_view(), name='order-create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('payment/order/<int:pk>/', csrf_exempt(views.PaymentWithStripeView.as_view()), name='checkout-session'),
    path('stripe-webhook/', views.stripe_webhook_view, name='stripe-webhook'),
    path('groups/manager/', views.GroupViewset.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy',
    }), name='group-manager'),
    path('groups/delivery-crew/', views.DeliveryCrewViewSet.as_view({
        'get': 'list', 'post': 'create', 'delete': 'destroy'}), name='delivery-crew'),
    path('confirm-email/<int:user_id>/<str:token>/', views.confirm_email, name='confirm_email'),
]
