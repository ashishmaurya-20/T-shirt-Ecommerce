# store/admin.py - Update to handle None values safely

from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'available', 'created']
    list_filter = ['available', 'created', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'old_price')
        }),
        ('Inventory', {
            'fields': ('stock', 'available')
        }),
        ('Sizes Available', {
            'fields': ('size_s', 'size_m', 'size_l', 'size_xl', 'size_xxl')
        }),
    )

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'size', 'display_cost']
    
    def display_cost(self, obj):
        try:
            cost = obj.get_cost()
            if cost is not None:
                return f'₹{cost}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_cost.short_description = 'Cost'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'get_total_items', 'display_total_price']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    inlines = [CartItemInline]
    
    def display_total_price(self, obj):
        try:
            total = obj.get_total_price()
            if total is not None:
                return f'₹{total}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_total_price.short_description = 'Total Price'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'size', 'display_cost']
    
    def display_cost(self, obj):
        try:
            cost = obj.get_cost()
            if cost is not None:
                return f'₹{cost}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_cost.short_description = 'Cost'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'display_total_amount', 'paid', 'created']
    list_filter = ['paid', 'created']
    search_fields = ['first_name', 'last_name', 'email', 'payment_id']
    inlines = [OrderItemInline]
    readonly_fields = ['payment_id', 'razorpay_order_id', 'payment_signature', 'created', 'display_total_amount']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('Order Information', {
            'fields': ('display_total_amount', 'paid', 'created')
        }),
        ('Payment Information', {
            'fields': ('payment_id', 'razorpay_order_id', 'payment_signature'),
            'classes': ('collapse',)
        }),
    )
    
    def display_total_amount(self, obj):
        try:
            if obj.total_amount and obj.total_amount > 0:
                return f'₹{obj.total_amount}'
            # If total_amount is not set, calculate from items
            total = obj.get_total_cost()
            if total and total > 0:
                return f'₹{total}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_total_amount.short_description = 'Total Amount'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'size', 'quantity', 'display_price', 'display_cost']
    list_filter = ['size']
    search_fields = ['order__id', 'product__name']
    
    def display_price(self, obj):
        try:
            if obj.price is not None:
                return f'₹{obj.price}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_price.short_description = 'Price'
    
    def display_cost(self, obj):
        try:
            cost = obj.get_cost()
            if cost is not None:
                return f'₹{cost}'
            return '₹0'
        except (TypeError, AttributeError):
            return '₹0'
    display_cost.short_description = 'Total'