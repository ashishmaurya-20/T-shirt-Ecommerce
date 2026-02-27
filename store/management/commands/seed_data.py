# store/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help = 'Seed database with sample products'
    
    def handle(self, *args, **kwargs):
        # Create categories
        category = Category.objects.create(
            name='Classic Tees',
            slug='classic-tees',
            description='Our classic collection'
        )
        
        # Create products
        products = [
            {
                'name': 'slub jersey tee',
                'slug': 'slub-jersey-tee',
                'description': 'Soft and comfortable slub jersey fabric',
                'price': 34,
                'old_price': 48,
                'size_s': True,
                'size_m': True,
                'size_l': True,
                'size_xl': True,
                'size_xxl': True,
            },
            # Add more products...
        ]
        
        for product_data in products:
            Product.objects.create(category=category, **product_data)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))