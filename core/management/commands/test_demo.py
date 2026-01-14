#!/usr/bin/env python
"""
FeedsHub POS - Demo Data Setup Script
Creates complete demo environments for different market types:
1. Mini-Shop/Duka
2. Pharmacy
3. Boutique/Clothing Shop

Run with: python manage.py shell < create_demo_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_backend.settings')
django.setup()

from core.models import (
    User, Role, Category, Product, Supplier,
    Sale, SaleItem, Payment, StockMovement,
    PurchaseOrder, PurchaseOrderItem, Store
)
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
import random

def clear_existing_data():
    """Clear existing demo data"""
    print("\n🧹 Clearing existing demo data...")
    
    # Delete in correct order to respect foreign keys
    SaleItem.objects.all().delete()
    Payment.objects.all().delete()
    Sale.objects.all().delete()
    PurchaseOrderItem.objects.all().delete()
    PurchaseOrder.objects.all().delete()
    StockMovement.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Supplier.objects.all().delete()
    
    # Keep users and roles
    print("✅ Cleared demo data (kept users and roles)")

def get_or_create_store():
    """Ask user for store selection or create new store"""
    print("\n🎯 Multi-Store Demo Setup")
    existing_stores = Store.objects.all()
    
    if existing_stores.exists():
        print("\nExisting demo stores:")
        for idx, s in enumerate(existing_stores, start=1):
            print(f"{idx}. {s.name}")
    
    choice = input("\nDo you want to (1) use existing store or (2) create new store? [1/2]: ").strip()
    
    if choice == '1' and existing_stores.exists():
        store_idx = int(input("Enter store number: ").strip()) - 1
        store = existing_stores[store_idx]
        print(f"Using existing store: {store.name}")
        return store
    else:
        store_name = input("Enter new store name: ").strip()
        store_desc = input("Enter store description (optional): ").strip()
        store = Store.objects.create(name=store_name, description=store_desc)
        print(f"✅ Created new store: {store.name}")
        return store

def create_mini_shop_demo():
    """Create demo data for Mini-Shop/Duka"""
    print("\n🏪 Creating Mini-Shop/Duka Demo Data...")
    
    # Categories
    categories = {
        'beverages': Category.objects.create(
            name='Beverages',
            description='Soft drinks, water, juices'
        ),
        'groceries': Category.objects.create(
            name='Groceries',
            description='Rice, flour, cooking oil, sugar'
        ),
        'snacks': Category.objects.create(
            name='Snacks',
            description='Biscuits, crisps, sweets'
        ),
        'household': Category.objects.create(
            name='Household Items',
            description='Soap, detergent, toilet paper'
        ),
        'dairy': Category.objects.create(
            name='Dairy Products',
            description='Milk, butter, cheese'
        ),
    }
    
    # Suppliers
    suppliers = {
        'kamili': Supplier.objects.create(
            name='Kamili Distributors',
            contact_person='John Kamau',
            phone='0722123456',
            email='kamili@example.com'
        ),
        'bidco': Supplier.objects.create(
            name='Bidco Africa Ltd',
            contact_person='Mary Wanjiru',
            phone='0733234567',
            email='bidco@example.com'
        ),
    }
    
    # Get admin user
    admin = User.objects.filter(role__name='admin').first()
    
    # Products - Mix of simple and bulk products
    products = []
    
    # Bulk products (parent-child)
    rice_parent = Product.objects.create(
        name='Rice 25kg Bag',
        sku='RICE-25KG-BULK',
        category=categories['groceries'],
        product_type='parent',
        base_unit='kg',
        unit_quantity=Decimal('25'),
        price=Decimal('2500.00'),
        cost_price=Decimal('2000.00'),
        stock_quantity=20,
        min_stock_level=5,
        created_by=admin
    )
    
    # Child products for rice
    rice_children = [
        {'qty': '1', 'price': '120', 'cost': '95'},
        {'qty': '2', 'price': '230', 'cost': '185'},
        {'qty': '5', 'price': '550', 'cost': '450'},
    ]
    
    for child in rice_children:
        qty = Decimal(child['qty'])
        Product.objects.create(
            name=f"Rice {child['qty']}kg",
            sku=f"RICE-{child['qty']}KG",
            category=categories['groceries'],
            product_type='child',
            parent_product=rice_parent,
            base_unit='kg',
            unit_quantity=qty,
            conversion_factor=qty / rice_parent.unit_quantity,
            price=Decimal(child['price']),
            cost_price=Decimal(child['cost']),
            min_stock_level=20,
            created_by=admin
        )
    
    # Cooking oil bulk
    oil_parent = Product.objects.create(
        name='Cooking Oil 20L Jerry Can',
        sku='OIL-20L-BULK',
        category=categories['groceries'],
        product_type='parent',
        base_unit='l',
        unit_quantity=Decimal('20'),
        price=Decimal('3200.00'),
        cost_price=Decimal('2800.00'),
        stock_quantity=15,
        min_stock_level=5,
        created_by=admin
    )
    
    oil_children = [
        {'qty': '0.5', 'price': '95', 'cost': '80'},
        {'qty': '1', 'price': '180', 'cost': '150'},
        {'qty': '2', 'price': '350', 'cost': '295'},
    ]
    
    for child in oil_children:
        qty = Decimal(child['qty'])
        if qty < 1:
            name = f"Cooking Oil {int(qty * 1000)}ml"
        else:
            name = f"Cooking Oil {child['qty']}L"
        
        Product.objects.create(
            name=name,
            sku=f"OIL-{child['qty']}L",
            category=categories['groceries'],
            product_type='child',
            parent_product=oil_parent,
            base_unit='l',
            unit_quantity=qty,
            conversion_factor=qty / oil_parent.unit_quantity,
            price=Decimal(child['price']),
            cost_price=Decimal(child['cost']),
            min_stock_level=25,
            created_by=admin
        )
    
    # Simple products
    simple_products = [
        # Beverages
        {'name': 'Coca-Cola 500ml', 'sku': 'COKE-500', 'cat': 'beverages', 
         'price': '50', 'cost': '40', 'stock': 100},
        {'name': 'Dasani Water 500ml', 'sku': 'WATER-500', 'cat': 'beverages',
         'price': '30', 'cost': '22', 'stock': 150},
        {'name': 'Fanta Orange 500ml', 'sku': 'FANTA-500', 'cat': 'beverages',
         'price': '50', 'cost': '40', 'stock': 80},
        
        # Snacks
        {'name': 'Biscuits 200g', 'sku': 'BISC-200', 'cat': 'snacks',
         'price': '60', 'cost': '45', 'stock': 120},
        {'name': 'Crisps 100g', 'sku': 'CRISP-100', 'cat': 'snacks',
         'price': '40', 'cost': '30', 'stock': 200},
        
        # Household
        {'name': 'Bar Soap 250g', 'sku': 'SOAP-250', 'cat': 'household',
         'price': '45', 'cost': '35', 'stock': 150},
        {'name': 'Washing Powder 1kg', 'sku': 'POWDER-1KG', 'cat': 'household',
         'price': '180', 'cost': '145', 'stock': 80},
        
        # Dairy
        {'name': 'Fresh Milk 500ml', 'sku': 'MILK-500', 'cat': 'dairy',
         'price': '70', 'cost': '55', 'stock': 50},
        {'name': 'Margarine 500g', 'sku': 'MARG-500', 'cat': 'dairy',
         'price': '150', 'cost': '120', 'stock': 60},
    ]
    
    for p in simple_products:
        products.append(
            Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=categories[p['cat']],
                product_type='simple',
                price=Decimal(p['price']),
                cost_price=Decimal(p['cost']),
                stock_quantity=int(p['stock']),
                min_stock_level=20,
                created_by=admin
            )
        )
    
    # Create sample sales
    cashier = User.objects.filter(role__name='cashier').first() or admin
    
    for i in range(5):
        sale = Sale.objects.create(
            cashier=cashier,
            customer_name=f'Customer {i+1}',
            subtotal=Decimal('0'),
            total=Decimal('0'),
            payment_method=random.choice(['cash', 'mobile']),
            amount_paid=Decimal('0'),
            status='completed'
        )
        
        # Add 2-4 items per sale
        sale_items = random.sample(products[:8], random.randint(2, 4))
        subtotal = Decimal('0')
        
        for product in sale_items:
            qty = random.randint(1, 3)
            unit_price = product.price
            item_subtotal = unit_price * qty
            subtotal += item_subtotal
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=qty,
                unit_price=unit_price,
                subtotal=item_subtotal
            )
        
        sale.subtotal = subtotal
        sale.total = subtotal
        sale.amount_paid = subtotal
        sale.save()
        
        Payment.objects.create(
            sale=sale,
            payment_method=sale.payment_method,
            amount=subtotal
        )
    
    print("✅ Mini-Shop demo data created!")
    print(f"   - {len(categories)} categories")
    print(f"   - {len(suppliers)} suppliers")
    print(f"   - {Product.objects.count()} products (including bulk)")
    print(f"   - {Sale.objects.count()} sample sales")


def create_pharmacy_demo():
    """Create demo data for Pharmacy"""
    print("\n💊 Creating Pharmacy Demo Data...")
    
    # Categories
    categories = {
        'prescription': Category.objects.create(
            name='Prescription Medicines',
            description='Requires prescription'
        ),
        'otc': Category.objects.create(
            name='Over-the-Counter',
            description='General medications'
        ),
        'supplements': Category.objects.create(
            name='Vitamins & Supplements',
            description='Health supplements'
        ),
        'personal_care': Category.objects.create(
            name='Personal Care',
            description='First aid, hygiene'
        ),
    }
    
    # Suppliers
    suppliers = {
        'cosmos': Supplier.objects.create(
            name='Cosmos Pharmaceuticals',
            contact_person='Dr. James Ochieng',
            phone='0722345678',
            email='cosmos@pharmacy.ke'
        ),
        'dawa': Supplier.objects.create(
            name='Dawa Limited',
            contact_person='Susan Muthoni',
            phone='0733456789',
            email='dawa@supplies.ke'
        ),
    }
    
    admin = User.objects.filter(role__name='admin').first()
    
    # Products with batch tracking info in description
    products = [
        # Prescription
        {'name': 'Amoxicillin 500mg (30 tabs)', 'sku': 'AMOX-500-30', 'cat': 'prescription',
         'price': '450', 'cost': '350', 'stock': 50, 'desc': 'Batch: AMX2024-01 | Exp: 2025-12'},
        {'name': 'Metformin 500mg (60 tabs)', 'sku': 'MET-500-60', 'cat': 'prescription',
         'price': '350', 'cost': '280', 'stock': 40, 'desc': 'Batch: MET2024-02 | Exp: 2026-03'},
        {'name': 'Lisinopril 10mg (30 tabs)', 'sku': 'LIS-10-30', 'cat': 'prescription',
         'price': '550', 'cost': '450', 'stock': 35, 'desc': 'Batch: LIS2024-01 | Exp: 2025-11'},
        
        # OTC
        {'name': 'Paracetamol 500mg (20 tabs)', 'sku': 'PARA-500-20', 'cat': 'otc',
         'price': '80', 'cost': '60', 'stock': 200, 'desc': 'Batch: PAR2024-05 | Exp: 2026-06'},
        {'name': 'Ibuprofen 400mg (20 tabs)', 'sku': 'IBU-400-20', 'cat': 'otc',
         'price': '150', 'cost': '120', 'stock': 150, 'desc': 'Batch: IBU2024-03 | Exp: 2026-01'},
        {'name': 'Cough Syrup 100ml', 'sku': 'COUGH-100', 'cat': 'otc',
         'price': '250', 'cost': '200', 'stock': 80, 'desc': 'Batch: CS2024-02 | Exp: 2025-09'},
        
        # Supplements
        {'name': 'Vitamin C 1000mg (30 tabs)', 'sku': 'VIT-C-1000', 'cat': 'supplements',
         'price': '800', 'cost': '650', 'stock': 100, 'desc': 'Batch: VC2024-01 | Exp: 2027-12'},
        {'name': 'Multivitamin (60 caps)', 'sku': 'MULTI-60', 'cat': 'supplements',
         'price': '1200', 'cost': '950', 'stock': 75, 'desc': 'Batch: MV2024-04 | Exp: 2027-06'},
        
        # Personal Care
        {'name': 'First Aid Kit', 'sku': 'FIRSTAID-KIT', 'cat': 'personal_care',
         'price': '1500', 'cost': '1200', 'stock': 30, 'desc': 'Complete basic kit'},
        {'name': 'Digital Thermometer', 'sku': 'THERMO-DIG', 'cat': 'personal_care',
         'price': '800', 'cost': '600', 'stock': 45, 'desc': 'Fast-read digital'},
    ]
    
    product_objects = []
    for p in products:
        product_objects.append(
            Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=categories[p['cat']],
                description=p['desc'],
                product_type='simple',
                price=Decimal(p['price']),
                cost_price=Decimal(p['cost']),
                stock_quantity=int(p['stock']),
                min_stock_level=15,
                created_by=admin
            )
        )
    
    # Sample sales with customer tracking
    cashier = User.objects.filter(role__name='cashier').first() or admin
    customers = ['Alice Wambui', 'John Mwangi', 'Sarah Akinyi', 'David Kimani']
    
    for i in range(8):
        sale = Sale.objects.create(
            cashier=cashier,
            customer_name=random.choice(customers),
            subtotal=Decimal('0'),
            total=Decimal('0'),
            payment_method=random.choice(['cash', 'mobile', 'card']),
            amount_paid=Decimal('0'),
            status='completed',
            notes='Insurance: NHIF' if random.random() > 0.5 else ''
        )
        
        # Prescription sales typically have 1-3 items
        sale_items = random.sample(product_objects, random.randint(1, 3))
        subtotal = Decimal('0')
        
        for product in sale_items:
            qty = 1  # Pharmacies typically sell exact quantities
            unit_price = product.price
            item_subtotal = unit_price * qty
            subtotal += item_subtotal
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=qty,
                unit_price=unit_price,
                subtotal=item_subtotal
            )
        
        sale.subtotal = subtotal
        sale.total = subtotal
        sale.amount_paid = subtotal
        sale.save()
        
        Payment.objects.create(
            sale=sale,
            payment_method=sale.payment_method,
            amount=subtotal
        )
    
    print("✅ Pharmacy demo data created!")
    print(f"   - {len(categories)} categories")
    print(f"   - {len(suppliers)} suppliers")
    print(f"   - {len(product_objects)} products with batch tracking")
    print(f"   - {Sale.objects.count()} prescription sales")


def create_boutique_demo():
    """Create demo data for Boutique/Clothing Shop"""
    print("\n👗 Creating Boutique/Clothing Shop Demo Data...")
    
    # Categories
    categories = {
        'mens': Category.objects.create(
            name="Men's Clothing",
            description='Shirts, trousers, suits'
        ),
        'womens': Category.objects.create(
            name="Women's Clothing",
            description='Dresses, blouses, skirts'
        ),
        'kids': Category.objects.create(
            name="Kids' Clothing",
            description='Children apparel'
        ),
        'accessories': Category.objects.create(
            name='Accessories',
            description='Bags, belts, scarves'
        ),
    }
    
    # Suppliers
    suppliers = {
        'fashion': Supplier.objects.create(
            name='Fashion Imports Ltd',
            contact_person='Grace Njeri',
            phone='0722567890',
            email='fashion@imports.ke'
        ),
        'textile': Supplier.objects.create(
            name='Textile Traders',
            contact_person='Peter Omondi',
            phone='0733678901',
            email='textile@traders.ke'
        ),
    }
    
    admin = User.objects.filter(role__name='admin').first()
    
    # Products with size/color variants in name and description
    products = [
        # Men's
        {'name': 'Formal Shirt - Blue L', 'sku': 'SHIRT-BLU-L', 'cat': 'mens',
         'price': '1200', 'cost': '900', 'stock': 15, 'desc': 'Size: L | Color: Blue | Brand: Arrow'},
        {'name': 'Formal Shirt - White M', 'sku': 'SHIRT-WHT-M', 'cat': 'mens',
         'price': '1200', 'cost': '900', 'stock': 20, 'desc': 'Size: M | Color: White | Brand: Arrow'},
        {'name': 'Denim Jeans - Blue 32', 'sku': 'JEANS-BLU-32', 'cat': 'mens',
         'price': '2500', 'cost': '1900', 'stock': 12, 'desc': 'Size: 32 | Color: Blue | Brand: Levi'},
        
        # Women's
        {'name': 'Floral Dress - Red M', 'sku': 'DRESS-RED-M', 'cat': 'womens',
         'price': '2800', 'cost': '2100', 'stock': 8, 'desc': 'Size: M | Color: Red | Brand: Zara'},
        {'name': 'Blouse - White S', 'sku': 'BLOUSE-WHT-S', 'cat': 'womens',
         'price': '1500', 'cost': '1100', 'stock': 18, 'desc': 'Size: S | Color: White | Brand: H&M'},
        {'name': 'Maxi Skirt - Black L', 'sku': 'SKIRT-BLK-L', 'cat': 'womens',
         'price': '1800', 'cost': '1350', 'stock': 10, 'desc': 'Size: L | Color: Black'},
        
        # Kids
        {'name': 'Kids T-Shirt - Blue 8Y', 'sku': 'KTSH-BLU-8Y', 'cat': 'kids',
         'price': '600', 'cost': '450', 'stock': 25, 'desc': 'Age: 8 Years | Color: Blue'},
        {'name': 'Kids Shorts - Navy 10Y', 'sku': 'KSHRT-NAV-10Y', 'cat': 'kids',
         'price': '800', 'cost': '600', 'stock': 20, 'desc': 'Age: 10 Years | Color: Navy'},
        
        # Accessories
        {'name': 'Leather Belt - Brown', 'sku': 'BELT-BRN', 'cat': 'accessories',
         'price': '950', 'cost': '700', 'stock': 30, 'desc': 'Color: Brown | Genuine leather'},
        {'name': 'Handbag - Black', 'sku': 'BAG-BLK', 'cat': 'accessories',
         'price': '3500', 'cost': '2700', 'stock': 12, 'desc': 'Color: Black | Designer style'},
    ]
    
    product_objects = []
    for p in products:
        product_objects.append(
            Product.objects.create(
                name=p['name'],
                sku=p['sku'],
                category=categories[p['cat']],
                description=p['desc'],
                product_type='simple',
                price=Decimal(p['price']),
                cost_price=Decimal(p['cost']),
                stock_quantity=int(p['stock']),
                min_stock_level=5,
                created_by=admin
            )
        )
    
    # Sample sales with loyalty customers and store credit scenarios
    cashier = User.objects.filter(role__name='cashier').first() or admin
    loyalty_customers = [
        'Jane Kamau (VIP)',
        'Mary Wanjiku (Regular)',
        'Susan Achieng (New)',
        'Lucy Nyambura (VIP)'
    ]
    
    for i in range(6):
        customer_name = random.choice(loyalty_customers)
        is_vip = 'VIP' in customer_name
        
        sale = Sale.objects.create(
            cashier=cashier,
            customer_name=customer_name,
            subtotal=Decimal('0'),
            discount_amount=Decimal('0'),
            total=Decimal('0'),
            payment_method=random.choice(['cash', 'mobile', 'card']),
            amount_paid=Decimal('0'),
            status='completed',
            notes='Store Credit: KSh 500' if i == 2 else ('10% Loyalty Discount' if is_vip else '')
        )
        
        # Clothing sales usually have 1-3 items
        sale_items = random.sample(product_objects, random.randint(1, 3))
        subtotal = Decimal('0')
        
        for product in sale_items:
            qty = 1  # Usually 1 piece per item in clothing
            unit_price = product.price
            discount = 10 if is_vip else 0
            
            item_subtotal = (unit_price * qty) * (Decimal('100') - Decimal(str(discount))) / Decimal('100')
            subtotal += item_subtotal
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                quantity=qty,
                unit_price=unit_price,
                discount_percent=Decimal(str(discount)),
                subtotal=item_subtotal
            )
        
        sale.subtotal = subtotal
        sale.discount_amount = subtotal * Decimal('0.1') if is_vip else Decimal('0')
        sale.total = subtotal
        sale.amount_paid = subtotal
        sale.save()
        
        Payment.objects.create(
            sale=sale,
            payment_method=sale.payment_method,
            amount=subtotal
        )
    
    print("✅ Boutique demo data created!")
    print(f"   - {len(categories)} categories")
    print(f"   - {len(suppliers)} suppliers")
    print(f"   - {len(product_objects)} products (with variants)")
    print(f"   - {Sale.objects.count()} sales (with loyalty tracking)")


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🎯 FeedsHub POS - Demo Data Setup")
    print("="*70)
    
    try:
        with transaction.atomic():
            clear_existing_data()
            
            print("\nSelect demo type to create:")
            print("1. Mini-Shop/Duka")
            print("2. Pharmacy")
            print("3. Boutique/Clothing Shop")
            print("4. All demos")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == '1':
                create_mini_shop_demo()
            elif choice == '2':
                create_pharmacy_demo()
            elif choice == '3':
                create_boutique_demo()
            elif choice == '4':
                create_mini_shop_demo()
                clear_existing_data()
                create_pharmacy_demo()
                clear_existing_data()
                create_boutique_demo()
            else:
                print("❌ Invalid choice")
                return
            
            print("\n" + "="*70)
            print("✅ Demo Data Setup Complete!")
            print("="*70)
            print("\n📊 Summary:")
            print(f"   Categories: {Category.objects.count()}")
            print(f"   Suppliers: {Supplier.objects.count()}")
            print(f"   Products: {Product.objects.count()}")
            print(f"   Sales: {Sale.objects.count()}")
            print("\n💡 You can now explore the demo data in the system!")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == '__main__':
    main()