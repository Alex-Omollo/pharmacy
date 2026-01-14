# core/management/commands/create_bulk_product_example.py

from django.core.management.base import BaseCommand
from core.models import Product, Category, User
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create example bulk products with parent-child relationships'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('\n🏪 Creating Bulk Product Examples...\n'))
        
        # Get or create category
        category, _ = Category.objects.get_or_create(
            name='Food & Beverages',
            defaults={'description': 'Food items and beverages'}
        )
        
        # Get admin user as creator
        try:
            admin = User.objects.filter(is_superuser=True).first() or User.objects.first()
        except:
            self.stdout.write(self.style.ERROR('❌ No users found. Create users first.'))
            return
        
        # Example 1: Rice in bulk
        self.stdout.write('\n📦 Creating Rice Products...')
        
        # Create parent: 50kg Rice Bag
        rice_parent, created = Product.objects.get_or_create(
            sku='RICE-50KG-PARENT',
            defaults={
                'name': 'Rice 50kg Bag (Bulk)',
                'category': category,
                'description': 'Bulk rice bag - 50kg',
                'product_type': 'parent',
                'base_unit': 'kg',
                'unit_quantity': Decimal('50.000'),
                'price': Decimal('4500.00'),  # Wholesale price
                'cost_price': Decimal('3500.00'),
                'tax_rate': Decimal('0.00'),
                'stock_quantity': 5,  # 5 bags in stock
                'min_stock_level': 2,
                'is_active': True,
                'created_by': admin
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created parent: {rice_parent.name}'))
            self.stdout.write(f'    Stock: {rice_parent.stock_quantity} bags = {float(rice_parent.stock_quantity) * float(rice_parent.unit_quantity)}kg')
        
        # Create child products from parent
        rice_children = [
            {
                'name': 'Rice 500g',
                'sku': 'RICE-500G',
                'unit_quantity': Decimal('0.500'),
                'price': Decimal('55.00'),
                'cost_price': Decimal('40.00'),
            },
            {
                'name': 'Rice 1kg',
                'sku': 'RICE-1KG',
                'unit_quantity': Decimal('1.000'),
                'price': Decimal('105.00'),
                'cost_price': Decimal('75.00'),
            },
            {
                'name': 'Rice 2kg',
                'sku': 'RICE-2KG',
                'unit_quantity': Decimal('2.000'),
                'price': Decimal('200.00'),
                'cost_price': Decimal('145.00'),
            },
            {
                'name': 'Rice 5kg',
                'sku': 'RICE-5KG',
                'unit_quantity': Decimal('5.000'),
                'price': Decimal('475.00'),
                'cost_price': Decimal('350.00'),
            },
            {
                'name': 'Rice 10kg',
                'sku': 'RICE-10KG',
                'unit_quantity': Decimal('10.000'),
                'price': Decimal('925.00'),
                'cost_price': Decimal('680.00'),
            },
        ]
        
        for child_data in rice_children:
            conversion_factor = child_data['unit_quantity'] / rice_parent.unit_quantity
            
            child, created = Product.objects.get_or_create(
                sku=child_data['sku'],
                defaults={
                    'name': child_data['name'],
                    'category': category,
                    'description': f"Retail pack from {rice_parent.name}",
                    'product_type': 'child',
                    'parent_product': rice_parent,
                    'base_unit': 'kg',
                    'unit_quantity': child_data['unit_quantity'],
                    'conversion_factor': conversion_factor,
                    'price': child_data['price'],
                    'cost_price': child_data['cost_price'],
                    'tax_rate': Decimal('0.00'),
                    'stock_quantity': 0,
                    'min_stock_level': 10,
                    'is_active': True,
                    'created_by': admin
                }
            )
            
            if created:
                available = child.available_child_stock
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created child: {child.name}'))
                self.stdout.write(f'    Available: {available} units (from parent stock)')
        
        # Example 2: Cooking Oil
        self.stdout.write('\n🛢️  Creating Cooking Oil Products...')
        
        oil_parent, created = Product.objects.get_or_create(
            sku='OIL-20L-PARENT',
            defaults={
                'name': 'Cooking Oil 20L Jerry Can (Bulk)',
                'category': category,
                'description': 'Bulk cooking oil - 20 liters',
                'product_type': 'parent',
                'base_unit': 'l',
                'unit_quantity': Decimal('20.000'),
                'price': Decimal('3200.00'),
                'cost_price': Decimal('2500.00'),
                'tax_rate': Decimal('0.00'),
                'stock_quantity': 10,  # 10 jerry cans
                'min_stock_level': 3,
                'is_active': True,
                'created_by': admin
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Created parent: {oil_parent.name}'))
            self.stdout.write(f'    Stock: {oil_parent.stock_quantity} jerry cans = {float(oil_parent.stock_quantity) * float(oil_parent.unit_quantity)}L')
        
        oil_children = [
            {
                'name': 'Cooking Oil 500ml',
                'sku': 'OIL-500ML',
                'unit_quantity': Decimal('0.500'),
                'price': Decimal('95.00'),
                'cost_price': Decimal('70.00'),
            },
            {
                'name': 'Cooking Oil 1L',
                'sku': 'OIL-1L',
                'unit_quantity': Decimal('1.000'),
                'price': Decimal('180.00'),
                'cost_price': Decimal('135.00'),
            },
            {
                'name': 'Cooking Oil 2L',
                'sku': 'OIL-2L',
                'unit_quantity': Decimal('2.000'),
                'price': Decimal('350.00'),
                'cost_price': Decimal('260.00'),
            },
            {
                'name': 'Cooking Oil 5L',
                'sku': 'OIL-5L',
                'unit_quantity': Decimal('5.000'),
                'price': Decimal('850.00'),
                'cost_price': Decimal('640.00'),
            },
        ]
        
        for child_data in oil_children:
            conversion_factor = child_data['unit_quantity'] / oil_parent.unit_quantity
            
            child, created = Product.objects.get_or_create(
                sku=child_data['sku'],
                defaults={
                    'name': child_data['name'],
                    'category': category,
                    'description': f"Retail pack from {oil_parent.name}",
                    'product_type': 'child',
                    'parent_product': oil_parent,
                    'base_unit': 'l',
                    'unit_quantity': child_data['unit_quantity'],
                    'conversion_factor': conversion_factor,
                    'price': child_data['price'],
                    'cost_price': child_data['cost_price'],
                    'tax_rate': Decimal('0.00'),
                    'stock_quantity': 0,
                    'min_stock_level': 20,
                    'is_active': True,
                    'created_by': admin
                }
            )
            
            if created:
                available = child.available_child_stock
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created child: {child.name}'))
                self.stdout.write(f'    Available: {available} units (from parent stock)')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Bulk product examples created successfully!\n'))
        self.stdout.write(self.style.WARNING('📝 Summary:'))
        self.stdout.write('  - Parent products maintain bulk stock')
        self.stdout.write('  - Child products are derived from parent stock')
        self.stdout.write('  - Selling child products automatically reduces parent stock')
        self.stdout.write('  - You can sell in any unit size!\n')