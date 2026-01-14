# core/management/commands/setup_demo.py

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import (
    User, Role, Category, Product, Supplier, 
    Sale, SaleItem, Payment, StockMovement
)
from decimal import Decimal
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Setup demo data for different business types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business-type',
            type=str,
            choices=['mini-shop', 'pharmacy', 'boutique', 'all'],
            default='all',
            help='Type of business demo to setup'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before setup'
        )

    def handle(self, *args, **options):
        business_type = options['business_type']
        clear_data = options['clear']
        
        self.stdout.write(self.style.WARNING('\n🎬 Setting up Demo Data...\n'))
        
        if clear_data:
            self.clear_demo_data()
        
        # Setup base data (users, roles)
        self.setup_base_data()
        
        # Setup business-specific data
        if business_type == 'all' or business_type == 'mini-shop':
            self.setup_mini_shop_demo()
        
        if business_type == 'all' or business_type == 'pharmacy':
            self.setup_pharmacy_demo()
        
        if business_type == 'all' or business_type == 'boutique':
            self.setup_boutique_demo()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Demo setup complete!\n'))

    def clear_demo_data(self):
        self.stdout.write('🗑️  Clearing existing demo data...')
        # Keep admin users, clear other data
        Sale.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Supplier.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('   ✓ Demo data cleared\n'))

    def setup_base_data(self):
        self.stdout.write('👥 Setting up base users and roles...')
        
        # Ensure roles exist
        admin_role, _ = Role.objects.get_or_create(
            name='admin',
            defaults={'description': 'Full system access'}
        )
        manager_role, _ = Role.objects.get_or_create(
            name='manager',
            defaults={'description': 'Manager access'}
        )
        cashier_role, _ = Role.objects.get_or_create(
            name='cashier',
            defaults={'description': 'Cashier access'}
        )
        
        # Create demo users if they don't exist
        demo_admin, created = User.objects.get_or_create(
            username='demo_admin',
            defaults={
                'email': 'demo@feedshub.co.ke',
                'first_name': 'Demo',
                'last_name': 'Admin',
                'role': admin_role,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            demo_admin.set_password('demo123')
            demo_admin.save()
            self.stdout.write('   ✓ Demo admin created')

    def setup_mini_shop_demo(self):
        self.stdout.write('\n🏪 Setting up MINI-SHOP Demo...')
        
        # Categories for mini-shop
        categories = [
            ('Food & Beverages', 'Essential food items'),
            ('Household Items', 'Cleaning and household products'),
            ('Personal Care', 'Toiletries and personal care'),
            ('Snacks & Treats', 'Chips, biscuits, sweets'),
            ('Stationery', 'School and office supplies')
        ]
        
        cat_objects = {}
        for cat_name, desc in categories:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': desc}
            )
            cat_objects[cat_name] = cat
        
        # Suppliers
        suppliers = [
            ('Unga Limited', 'John Kamau', '0712345678', 'Flour and bakery products'),
            ('Bidco Africa', 'Mary Wanjiru', '0723456789', 'Cooking oil and soap'),
            ('Brookside Dairy', 'Peter Omondi', '0734567890', 'Milk and dairy products'),
            ('Coca-Cola Kenya', 'Jane Muthoni', '0745678901', 'Soft drinks')
        ]
        
        supplier_objects = []
        for name, contact, phone, desc in suppliers:
            supplier, _ = Supplier.objects.get_or_create(
                name=name,
                defaults={
                    'contact_person': contact,
                    'phone': phone,
                    'address': desc,
                    'is_active': True
                }
            )
            supplier_objects.append(supplier)
        
        # Products with realistic Kenyan pricing
        products_data = [
            # Food & Beverages
            ('Unga wa Dola 2kg', 'Food & Beverages', 195.00, 180.00, 50, 10),
            ('Maize Flour 1kg', 'Food & Beverages', 98.00, 90.00, 100, 20),
            ('Rice 1kg', 'Food & Beverages', 145.00, 130.00, 80, 15),
            ('Sugar 1kg', 'Food & Beverages', 165.00, 150.00, 60, 10),
            ('Cooking Oil 1L', 'Food & Beverages', 320.00, 290.00, 40, 8),
            ('Bread (Brown)', 'Food & Beverages', 55.00, 45.00, 30, 10),
            ('Fresh Milk 500ml', 'Food & Beverages', 65.00, 55.00, 50, 20),
            ('Tea Leaves 250g', 'Food & Beverages', 85.00, 75.00, 45, 10),
            
            # Household Items
            ('Omo Washing Powder 1kg', 'Household Items', 275.00, 250.00, 35, 8),
            ('Sunlight Soap Bar', 'Household Items', 45.00, 38.00, 100, 20),
            ('Jik Bleach 750ml', 'Household Items', 95.00, 85.00, 25, 5),
            ('Toilet Paper 4-pack', 'Household Items', 180.00, 160.00, 40, 10),
            
            # Personal Care
            ('Geisha Soap', 'Personal Care', 35.00, 28.00, 150, 30),
            ('Colgate Toothpaste', 'Personal Care', 125.00, 110.00, 50, 10),
            ('Vaseline Petroleum Jelly', 'Personal Care', 85.00, 75.00, 45, 10),
            
            # Snacks & Treats
            ('Bambino Biscuits', 'Snacks & Treats', 25.00, 20.00, 200, 50),
            ('Chipsy Chips 100g', 'Snacks & Treats', 45.00, 38.00, 150, 30),
            ('Lollipops Pack', 'Snacks & Treats', 50.00, 40.00, 100, 20),
            
            # Stationery
            ('Exercise Book 40-pages', 'Stationery', 35.00, 28.00, 100, 20),
            ('Pen (Blue)', 'Stationery', 15.00, 10.00, 200, 50),
            ('Pencils Pack of 10', 'Stationery', 85.00, 70.00, 50, 10),
        ]
        
        admin_user = User.objects.get(username='demo_admin')
        created_products = []
        
        for name, cat_name, price, cost, stock, min_stock in products_data:
            product, _ = Product.objects.get_or_create(
                name=name,
                defaults={
                    'sku': f'DEMO-{random.randint(1000, 9999)}',
                    'barcode': f'{random.randint(100000000000, 999999999999)}',
                    'category': cat_objects[cat_name],
                    'price': Decimal(str(price)),
                    'cost_price': Decimal(str(cost)),
                    'stock_quantity': stock,
                    'min_stock_level': min_stock,
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            created_products.append(product)
        
        # Generate sample sales (last 30 days)
        self.generate_mini_shop_sales(created_products, admin_user)
        
        self.stdout.write(self.style.SUCCESS('   ✓ Mini-shop demo data created'))

    def generate_mini_shop_sales(self, products, user):
        """Generate realistic sales data for mini-shop"""
        days = 30
        for day in range(days):
            date = datetime.now() - timedelta(days=days-day)
            # 5-15 sales per day
            num_sales = random.randint(5, 15)
            
            for _ in range(num_sales):
                # Random 1-5 items per sale
                num_items = random.randint(1, 5)
                sale_products = random.sample(products, min(num_items, len(products)))
                
                # Calculate totals
                subtotal = Decimal('0')
                items_data = []
                
                for product in sale_products:
                    quantity = random.randint(1, 3)
                    item_subtotal = product.price * quantity
                    subtotal += item_subtotal
                    items_data.append((product, quantity, item_subtotal))
                
                # Create sale
                payment_method = random.choice(['cash', 'mobile', 'cash', 'mobile'])
                
                with transaction.atomic():
                    sale = Sale.objects.create(
                        cashier=user,
                        customer_name=random.choice(['', '', 'John', 'Mary', 'Peter', 'Jane']),
                        subtotal=subtotal,
                        tax_amount=Decimal('0'),
                        discount_amount=Decimal('0'),
                        total=subtotal,
                        payment_method=payment_method,
                        amount_paid=subtotal,
                        change_amount=Decimal('0'),
                        status='completed'
                    )
                    sale.created_at = date
                    sale.save()
                    
                    # Create sale items
                    for product, quantity, item_subtotal in items_data:
                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            product_name=product.name,
                            product_sku=product.sku,
                            quantity=quantity,
                            unit_price=product.price,
                            tax_rate=Decimal('0'),
                            discount_percent=Decimal('0'),
                            subtotal=item_subtotal
                        )
                    
                    # Create payment
                    Payment.objects.create(
                        sale=sale,
                        payment_method=payment_method,
                        amount=subtotal
                    )

    def setup_pharmacy_demo(self):
        self.stdout.write('\n💊 Setting up PHARMACY Demo...')
        
        # Pharmacy-specific categories
        categories = [
            ('Prescription Drugs', 'Requires prescription'),
            ('Over-the-Counter', 'Available without prescription'),
            ('Vitamins & Supplements', 'Health supplements'),
            ('Medical Devices', 'Blood pressure monitors, thermometers'),
            ('Baby Care', 'Baby products and nutrition')
        ]
        
        cat_objects = {}
        for cat_name, desc in categories:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': desc}
            )
            cat_objects[cat_name] = cat
        
        # Pharmacy products with batch info and expiry
        products_data = [
            # Prescription Drugs
            ('Amoxicillin 500mg (30 tabs)', 'Prescription Drugs', 450.00, 380.00, 50, 10, True),
            ('Ciprofloxacin 500mg (10 tabs)', 'Prescription Drugs', 350.00, 290.00, 40, 8, True),
            ('Metformin 500mg (60 tabs)', 'Prescription Drugs', 280.00, 230.00, 60, 12, True),
            
            # Over-the-Counter
            ('Panadol (16 tabs)', 'Over-the-Counter', 85.00, 70.00, 150, 30, False),
            ('Mara Moja (1 tab)', 'Over-the-Counter', 50.00, 40.00, 200, 50, False),
            ('Piriton (30 tabs)', 'Over-the-Counter', 120.00, 100.00, 100, 20, False),
            ('Strepsils Lozenges', 'Over-the-Counter', 180.00, 150.00, 80, 15, False),
            
            # Vitamins & Supplements
            ('Vitamin C 1000mg', 'Vitamins & Supplements', 850.00, 720.00, 45, 10, False),
            ('Multivitamin Tabs', 'Vitamins & Supplements', 1200.00, 1000.00, 35, 8, False),
            ('Zinc Tablets', 'Vitamins & Supplements', 650.00, 550.00, 40, 10, False),
            
            # Medical Devices
            ('Digital Thermometer', 'Medical Devices', 450.00, 380.00, 25, 5, False),
            ('Blood Pressure Monitor', 'Medical Devices', 3500.00, 3000.00, 15, 3, False),
            
            # Baby Care
            ('Baby Formula 400g', 'Baby Care', 950.00, 820.00, 40, 10, False),
            ('Diapers Pack (Medium)', 'Baby Care', 1100.00, 950.00, 35, 8, False),
        ]
        
        admin_user = User.objects.get(username='demo_admin')
        
        for name, cat_name, price, cost, stock, min_stock, is_prescription in products_data:
            # Add prescription indicator to description
            description = ''
            if is_prescription:
                description = '⚕️ PRESCRIPTION REQUIRED - Must be dispensed by licensed pharmacist'
            
            Product.objects.get_or_create(
                name=name,
                defaults={
                    'sku': f'MED-{random.randint(1000, 9999)}',
                    'barcode': f'{random.randint(100000000000, 999999999999)}',
                    'category': cat_objects[cat_name],
                    'description': description,
                    'price': Decimal(str(price)),
                    'cost_price': Decimal(str(cost)),
                    'stock_quantity': stock,
                    'min_stock_level': min_stock,
                    'created_by': admin_user,
                    'is_active': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS('   ✓ Pharmacy demo data created'))

    def setup_boutique_demo(self):
        self.stdout.write('\n👗 Setting up BOUTIQUE Demo...')
        
        # Boutique categories
        categories = [
            ('Women\'s Clothing', 'Dresses, tops, skirts'),
            ('Men\'s Clothing', 'Shirts, trousers, suits'),
            ('Shoes', 'Footwear for all occasions'),
            ('Accessories', 'Bags, jewelry, belts'),
            ('Kids Wear', 'Children\'s clothing')
        ]
        
        cat_objects = {}
        for cat_name, desc in categories:
            cat, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'description': desc}
            )
            cat_objects[cat_name] = cat
        
        # Boutique products with sizes/colors
        products_data = [
            # Women's Clothing
            ('Floral Dress (M)', 'Women\'s Clothing', 1500.00, 1200.00, 5, 2),
            ('Floral Dress (L)', 'Women\'s Clothing', 1500.00, 1200.00, 5, 2),
            ('Casual Top (Red, M)', 'Women\'s Clothing', 850.00, 680.00, 8, 3),
            ('Casual Top (Blue, M)', 'Women\'s Clothing', 850.00, 680.00, 7, 3),
            ('Office Skirt (Black, M)', 'Women\'s Clothing', 1200.00, 950.00, 6, 2),
            
            # Men's Clothing
            ('Men Shirt (White, L)', 'Men\'s Clothing', 1100.00, 880.00, 10, 3),
            ('Men Shirt (Blue, L)', 'Men\'s Clothing', 1100.00, 880.00, 8, 3),
            ('Khaki Trousers (32)', 'Men\'s Clothing', 1800.00, 1440.00, 12, 4),
            ('Khaki Trousers (34)', 'Men\'s Clothing', 1800.00, 1440.00, 10, 4),
            
            # Shoes
            ('Ladies Heels (Size 38)', 'Shoes', 2200.00, 1800.00, 6, 2),
            ('Ladies Heels (Size 40)', 'Shoes', 2200.00, 1800.00, 5, 2),
            ('Men Leather Shoes (42)', 'Shoes', 3500.00, 2800.00, 8, 2),
            ('Canvas Shoes (39)', 'Shoes', 1500.00, 1200.00, 15, 5),
            
            # Accessories
            ('Leather Handbag (Brown)', 'Accessories', 2800.00, 2240.00, 10, 3),
            ('Leather Handbag (Black)', 'Accessories', 2800.00, 2240.00, 12, 3),
            ('Fashion Belt', 'Accessories', 650.00, 520.00, 20, 5),
            ('Earrings Set', 'Accessories', 450.00, 360.00, 25, 8),
            
            # Kids Wear
            ('Kids T-Shirt (Age 5-7)', 'Kids Wear', 450.00, 360.00, 20, 5),
            ('Kids Shorts (Age 8-10)', 'Kids Wear', 550.00, 440.00, 18, 5),
        ]
        
        admin_user = User.objects.get(username='demo_admin')
        
        for name, cat_name, price, cost, stock, min_stock in products_data:
            Product.objects.get_or_create(
                name=name,
                defaults={
                    'sku': f'BTQ-{random.randint(1000, 9999)}',
                    'barcode': f'{random.randint(100000000000, 999999999999)}',
                    'category': cat_objects[cat_name],
                    'price': Decimal(str(price)),
                    'cost_price': Decimal(str(cost)),
                    'stock_quantity': stock,
                    'min_stock_level': min_stock,
                    'created_by': admin_user,
                    'is_active': True
                }
            )
        
        self.stdout.write(self.style.SUCCESS('   ✓ Boutique demo data created'))