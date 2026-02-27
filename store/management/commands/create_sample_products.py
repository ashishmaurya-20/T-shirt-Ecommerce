# store/management/commands/create_sample_products.py
from django.core.management.base import BaseCommand
from store.models import Category, Product
from django.core.files import File
import os

class Command(BaseCommand):
    help = 'Create sample products for testing'
    
    def handle(self, *args, **kwargs):
        # Create categories
        categories = [
            {
                'name': 'Classic Tees',
                'slug': 'classic-tees',
                'description': 'Timeless classics for everyday wear'
            },
            {
                'name': 'Printed Tees',
                'slug': 'printed-tees',
                'description': 'Unique designs and patterns'
            },
            {
                'name': 'Premium Collection',
                'slug': 'premium',
                'description': 'High-quality premium t-shirts'
            },
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
        
        # Sample products
        products = [
            {
                'name': 'Slub Jersey Tee',
                'slug': 'slub-jersey-tee',
                'description': 'Soft and comfortable slub jersey fabric. Perfect for everyday wear.',
                'price': 999,
                'old_price': 1299,
                'category': 'classic-tees',
                'sizes': ['S', 'M', 'L', 'XL'],
            },
            {
                'name': 'Heavyweight Tee',
                'slug': 'heavyweight-tee',
                'description': 'Premium heavyweight cotton for durability and comfort.',
                'price': 1499,
                'old_price': 1999,
                'category': 'premium',
                'sizes': ['M', 'L', 'XL', 'XXL'],
            },
            {
                'name': 'Striped Pocket Tee',
                'slug': 'striped-pocket-tee',
                'description': 'Classic striped design with convenient chest pocket.',
                'price': 1199,
                'old_price': 1599,
                'category': 'printed-tees',
                'sizes': ['S', 'M', 'L', 'XL'],
            },
            {
                'name': 'Faded Organic Tee',
                'slug': 'faded-organic-tee',
                'description': 'Eco-friendly organic cotton with a vintage faded look.',
                'price': 1399,
                'old_price': 1799,
                'category': 'premium',
                'sizes': ['S', 'M', 'L', 'XL', 'XXL'],
            },
            {
                'name': 'Ringer Tee',
                'slug': 'ringer-tee',
                'description': 'Retro-style ringer tee with contrasting collar and cuffs.',
                'price': 899,
                'old_price': 1199,
                'category': 'classic-tees',
                'sizes': ['S', 'M', 'L'],
            },
        ]
        
        for prod_data in products:
            category = Category.objects.get(slug=prod_data['category'])
            
            # Set size availability
            size_defaults = {
                'size_s': 'S' in prod_data['sizes'],
                'size_m': 'M' in prod_data['sizes'],
                'size_l': 'L' in prod_data['sizes'],
                'size_xl': 'XL' in prod_data['sizes'],
                'size_xxl': 'XXL' in prod_data['sizes'],
            }
            
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    'name': prod_data['name'],
                    'category': category,
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'old_price': prod_data['old_price'],
                    'stock': 10,
                    'available': True,
                    **size_defaults
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {product.name}')
            else:
                self.stdout.write(f'Product already exists: {product.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample products!'))