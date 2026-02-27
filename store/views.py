# store/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import SignUpForm, LoginForm, AddToCartForm, OrderForm
import json

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def home(request):
    products = Product.objects.filter(available=True)[:12]
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'store/home.html', context)

@require_POST
def add_to_cart_ajax(request):
    """AJAX endpoint to add item to cart without page reload"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        size = data.get('size')
        
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Product added to cart',
            'cart_total': cart.get_total_items(),
            'cart_total_price': str(cart.get_total_price())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def create_razorpay_order(request):
    """Create Razorpay order for direct purchase"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            size = data.get('size')
            
            product = get_object_or_404(Product, id=product_id)
            amount = int(product.price * quantity * 100)  # Razorpay expects amount in paise
            
            # Create Razorpay Order
            razorpay_order = razorpay_client.order.create({
                'amount': amount,
                'currency': settings.RAZORPAY_CURRENCY,
                'payment_capture': '1'  # Auto capture payment
            })
            
            # Store order in session for verification
            request.session['pending_order'] = {
                'order_id': razorpay_order['id'],
                'product_id': product_id,
                'quantity': quantity,
                'size': size,
                'amount': amount,
                'product_name': product.name
            }
            
            return JsonResponse({
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': settings.RAZORPAY_CURRENCY,
                'key_id': settings.RAZORPAY_KEY_ID,
                'product_name': product.name,
                'description': f'{product.name} - Size {size}',
                'prefill': {
                    'name': request.user.get_full_name() if request.user.is_authenticated else '',
                    'email': request.user.email if request.user.is_authenticated else ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@csrf_exempt
def payment_success(request):
    """Handle successful payment"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data.get('razorpay_payment_id')
            order_id = data.get('razorpay_order_id')
            signature = data.get('razorpay_signature')
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({'success': False, 'error': 'Payment verification failed'}, status=400)
            
            # Get pending order from session
            pending_order = request.session.get('pending_order')
            if not pending_order:
                return JsonResponse({'success': False, 'error': 'No pending order found'}, status=400)
            
            # Create order in database
            product = get_object_or_404(Product, id=pending_order['product_id'])
            
            # Create order for authenticated user or guest
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=request.user.first_name if request.user.is_authenticated else 'Guest',
                last_name=request.user.last_name if request.user.is_authenticated else 'User',
                email=request.user.email if request.user.is_authenticated else 'guest@example.com',
                address='Pending - Will be collected separately',
                city='Pending',
                postal_code='000000',
                paid=True,
                payment_id=payment_id,
                razorpay_order_id=order_id
            )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=pending_order['quantity'],
                size=pending_order['size']
            )
            
            # Clear pending order from session
            del request.session['pending_order']
            
            return JsonResponse({
                'success': True,
                'message': 'Payment successful!',
                'order_id': order.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

def buy_now(request):
    """Handle buy now button - direct purchase"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            size = data.get('size')
            
            product = get_object_or_404(Product, id=product_id)
            
            # Create Razorpay order
            amount = int(product.price * quantity * 100)
            razorpay_order = razorpay_client.order.create({
                'amount': amount,
                'currency': settings.RAZORPAY_CURRENCY,
                'payment_capture': '1'
            })
            
            # Store in session
            request.session['pending_order'] = {
                'order_id': razorpay_order['id'],
                'product_id': product_id,
                'quantity': quantity,
                'size': size,
                'amount': amount,
                'product_name': product.name
            }
            
            return JsonResponse({
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': settings.RAZORPAY_CURRENCY,
                'key_id': settings.RAZORPAY_KEY_ID,
                'product_name': product.name,
                'description': f'{product.name} - Size {size}',
                'prefill': {
                    'name': request.user.get_full_name() if request.user.is_authenticated else '',
                    'email': request.user.email if request.user.is_authenticated else ''
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def home(request):
    products = Product.objects.filter(available=True)[:12]
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/home.html', context)

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    add_to_cart_form = AddToCartForm(product=product)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST, product=product)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            size = form.cleaned_data['size']
            
            # Add to cart logic
            cart = get_or_create_cart(request)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Product added to cart',
                    'cart_total': cart.get_total_items()
                })
            messages.success(request, 'Product added to cart successfully!')
            return redirect('store:cart_detail')
    
    context = {
        'product': product,
        'form': add_to_cart_form,
    }
    return render(request, 'store/product_detail.html', context)

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def cart_detail(request):
    cart = get_or_create_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})

@require_POST
def cart_add(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    size = data.get('size')
    
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'cart_total': cart.get_total_items(),
        'cart_total_price': str(cart.get_total_price())
    })

@require_POST
def cart_remove(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    
    cart = get_or_create_cart(request)
    return JsonResponse({
        'success': True,
        'cart_total': cart.get_total_items(),
        'cart_total_price': str(cart.get_total_price())
    })

@require_POST
def cart_update(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    quantity = int(data.get('quantity'))
    
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.quantity = quantity
    cart_item.save()
    
    return JsonResponse({
        'success': True,
        'item_total': str(cart_item.get_cost()),
        'cart_total': cart_item.cart.get_total_items(),
        'cart_total_price': str(cart_item.cart.get_total_price())
    })

# store/views.py

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import json
from .models import Product, Cart, CartItem, Order, OrderItem

# Initialize Razorpay client
try:
    razorpay_client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
except Exception as e:
    print(f"Razorpay initialization error: {e}")
    razorpay_client = None

def checkout(request):
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('store:home')
    
    # Check if Razorpay is configured
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, 'Payment gateway not configured. Please contact support.')
        return redirect('store:cart_detail')
    
    context = {
        'cart': cart,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'store/checkout.html', context)

@require_POST
def create_checkout_order(request):
    """Create Razorpay order for checkout"""
    try:
        # Check if Razorpay client is initialized
        if not razorpay_client:
            return JsonResponse({
                'success': False, 
                'error': 'Payment gateway not configured'
            }, status=500)
        
        data = json.loads(request.body)
        cart = get_or_create_cart(request)
        
        if not cart.items.exists():
            return JsonResponse({
                'success': False, 
                'error': 'Your cart is empty'
            }, status=400)
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'address', 'city', 'postal_code']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False, 
                    'error': f'{field} is required'
                }, status=400)
        
        # Calculate total amount
        total_amount = int(float(cart.get_total_price()) * 100)  # Convert to paise
        
        if total_amount <= 0:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid order amount'
            }, status=400)
        
        # Store shipping info in session temporarily
        request.session['checkout_info'] = {
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'email': data.get('email'),
            'address': data.get('address'),
            'city': data.get('city'),
            'postal_code': data.get('postal_code'),
        }
        
        # Create Razorpay Order
        razorpay_order = razorpay_client.order.create({
            'amount': total_amount,
            'currency': settings.RAZORPAY_CURRENCY,
            'payment_capture': '1',
            'notes': {
                'email': data.get('email'),
                'name': f"{data.get('first_name')} {data.get('last_name')}"
            }
        })
        
        # Store order in session for verification
        request.session['pending_checkout'] = {
            'razorpay_order_id': razorpay_order['id'],
            'amount': total_amount,
            'cart_total': float(cart.get_total_price()),
            'items': [
                {
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'size': item.size,
                    'price': float(item.product.price)
                }
                for item in cart.items.all()
            ]
        }
        
        return JsonResponse({
            'success': True,
            'order_id': razorpay_order['id'],
            'amount': total_amount,
            'currency': settings.RAZORPAY_CURRENCY,
            'key_id': settings.RAZORPAY_KEY_ID,
            'customer_info': {
                'name': f"{data.get('first_name')} {data.get('last_name')}",
                'email': data.get('email'),
                'contact': ''  # You can add phone number field if needed
            }
        })
        
    except razorpay.errors.BadRequestError as e:
        return JsonResponse({
            'success': False, 
            'error': f'Razorpay error: {str(e)}'
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid request data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }, status=500)

@csrf_exempt
def checkout_payment_success(request):
    """Handle successful payment for checkout"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data.get('razorpay_payment_id')
            order_id = data.get('razorpay_order_id')
            signature = data.get('razorpay_signature')
            
            if not all([payment_id, order_id, signature]):
                return JsonResponse({
                    'success': False, 
                    'error': 'Missing payment information'
                }, status=400)
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Payment signature verification failed'
                }, status=400)
            
            # Get pending checkout from session
            pending_checkout = request.session.get('pending_checkout')
            checkout_info = request.session.get('checkout_info')
            
            if not pending_checkout or not checkout_info:
                return JsonResponse({
                    'success': False, 
                    'error': 'Session expired. Please try again.'
                }, status=400)
            
            # Create order in database
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                first_name=checkout_info['first_name'],
                last_name=checkout_info['last_name'],
                email=checkout_info['email'],
                address=checkout_info['address'],
                city=checkout_info['city'],
                postal_code=checkout_info['postal_code'],
                paid=True,
                payment_id=payment_id,
                razorpay_order_id=order_id,
                payment_signature=signature,
                total_amount=pending_checkout['cart_total']
            )
            
            # Create order items from cart
            cart = get_or_create_cart(request)
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity,
                    size=item.size
                )
            
            # Clear cart and session data
            cart.items.all().delete()
            if 'pending_checkout' in request.session:
                del request.session['pending_checkout']
            if 'checkout_info' in request.session:
                del request.session['checkout_info']
            
            return JsonResponse({
                'success': True,
                'message': 'Payment successful!',
                'order_id': order.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Server error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    }, status=400)

# store/views.py - Add this view if missing

def order_confirmation(request, order_id):
    """Display order confirmation after successful payment"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Security: Check if user owns this order
        if request.user.is_authenticated:
            if order.user and order.user != request.user:
                messages.error(request, 'You do not have permission to view this order.')
                return redirect('store:home')
        else:
            # For guest checkout, you might want additional verification
            # For now, just show the order
            pass
            
        context = {
            'order': order
        }
        return render(request, 'store/order_confirmation.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('store:home')

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('store:home')
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Transfer session cart to user cart
                session_key = request.session.session_key
                if session_key:
                    try:
                        session_cart = Cart.objects.get(session_key=session_key)
                        user_cart, created = Cart.objects.get_or_create(user=user)
                        
                        # Move items from session cart to user cart
                        for item in session_cart.items.all():
                            user_item, created = CartItem.objects.get_or_create(
                                cart=user_cart,
                                product=item.product,
                                size=item.size,
                                defaults={'quantity': item.quantity}
                            )
                            if not created:
                                user_item.quantity += item.quantity
                                user_item.save()
                        
                        session_cart.delete()
                    except Cart.DoesNotExist:
                        pass
                
                messages.success(request, f'Welcome back, {username}!')
                return redirect('store:home')
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('store:home')