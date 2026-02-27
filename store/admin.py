# store/admin.py
from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem

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
    readonly_fields = ['product', 'quantity', 'size', 'get_cost']
    
    def get_cost(self, obj):
        return f'₹{obj.get_cost()}'
    get_cost.short_description = 'Cost'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'get_total_items', 'get_total_price']
    list_filter = ['created_at']
    search_fields = ['user__username', 'session_key']
    inlines = [CartItemInline]
    
    def get_total_price(self, obj):
        return f'₹{obj.get_total_price()}'
    get_total_price.short_description = 'Total Price'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'size', 'get_cost']
    
    def get_cost(self, obj):
        return f'₹{obj.get_cost()}'
    get_cost.short_description = 'Cost'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'total_amount', 'paid', 'created']
    list_filter = ['paid', 'created']
    search_fields = ['first_name', 'last_name', 'email', 'payment_id']
    inlines = [OrderItemInline]
    readonly_fields = ['payment_id', 'razorpay_order_id', 'payment_signature', 'created']
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('Order Information', {
            'fields': ('total_amount', 'paid', 'created')
        }),
        ('Payment Information', {
            'fields': ('payment_id', 'razorpay_order_id', 'payment_signature'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'size', 'quantity', 'price', 'get_cost']
    list_filter = ['size']
    search_fields = ['order__id', 'product__name']
    
    def get_cost(self, obj):
        return f'₹{obj.get_cost()}'
    get_cost.short_description = 'Total'