# store/urls.py - Make sure this exists
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/add/ajax/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('cart/remove/', views.cart_remove, name='cart_remove'),
    path('cart/update/', views.cart_update, name='cart_update'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/', views.order_confirmation, name='order_confirmation'),  # This line is critical
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Razorpay endpoints
    path('create-razorpay-order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('create-checkout-order/', views.create_checkout_order, name='create_checkout_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('checkout-payment-success/', views.checkout_payment_success, name='checkout_payment_success'),
    path('buy-now/', views.buy_now, name='buy_now'),
]