# core/management/commands/refresh_child_stock.py

from django.core.management.base import BaseCommand
from core.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Refresh and display child product stock availability from parent products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--parent-id',
            type=int,
            help='Refresh only children of specific parent product',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        parent_id = options.get('parent_id')
        verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.WARNING('\n🔄 Refreshing Child Product Stock...\n'))
        
        # Get parent products
        if parent_id:
            try:
                parents = Product.objects.filter(id=parent_id, product_type='parent')
                if not parents.exists():
                    self.stdout.write(self.style.ERROR(f'❌ Parent product with ID {parent_id} not found'))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
                return
        else:
            parents = Product.objects.filter(product_type='parent')
        
        if not parents.exists():
            self.stdout.write(self.style.WARNING('⚠️  No parent products found'))
            return
        
        total_parents = 0
        total_children = 0
        
        for parent in parents:
            total_parents += 1
            children = parent.child_products.filter(is_active=True)
            
            if not children.exists():
                if verbose:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  {parent.name} has no child products'))
                continue
            
            self.stdout.write(self.style.SUCCESS(f'\n📦 Parent: {parent.name}'))
            self.stdout.write(f'   Stock: {parent.stock_quantity} units × {parent.unit_quantity}{parent.base_unit}')
            
            # Calculate total in base units
            total_base = Decimal(str(parent.stock_quantity)) * parent.unit_quantity
            self.stdout.write(f'   Total: {total_base}{parent.base_unit} available')
            
            if parent.stock_quantity == 0:
                self.stdout.write(self.style.ERROR(f'   ⚠️  Parent is OUT OF STOCK - all children will show 0 availability'))
            
            self.stdout.write('\n   Children:')
            
            for child in children:
                total_children += 1
                available = child.available_child_stock
                
                # Status indicator
                if available == 0:
                    status = self.style.ERROR('OUT OF STOCK')
                elif child.is_low_stock:
                    status = self.style.WARNING('LOW STOCK')
                else:
                    status = self.style.SUCCESS('IN STOCK')
                
                self.stdout.write(
                    f'   ├─ {child.name} ({child.unit_quantity}{child.base_unit}): '
                    f'{available} units {status}'
                )
                
                if verbose:
                    # Show calculation
                    self.stdout.write(
                        f'   │  Calculation: {total_base}{parent.base_unit} ÷ '
                        f'{child.unit_quantity}{child.base_unit} = {available} units'
                    )
                    self.stdout.write(
                        f'   │  Price: ${child.price} | Min Stock: {child.min_stock_level}'
                    )
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Refresh Complete!'))
        self.stdout.write(f'   Parents processed: {total_parents}')
        self.stdout.write(f'   Children processed: {total_children}\n')
        
        # Summary of issues
        out_of_stock_parents = Product.objects.filter(
            product_type='parent',
            stock_quantity=0
        ).count()
        
        if out_of_stock_parents > 0:
            self.stdout.write(self.style.ERROR(
                f'⚠️  Warning: {out_of_stock_parents} parent product(s) are out of stock!'
            ))
        
        # Low stock children
        low_stock_children = []
        for parent in parents:
            for child in parent.child_products.filter(is_active=True):
                if child.is_low_stock and child.available_child_stock > 0:
                    low_stock_children.append(child)
        
        if low_stock_children:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  {len(low_stock_children)} child product(s) are running low:'
            ))
            for child in low_stock_children[:5]:  # Show first 5
                self.stdout.write(
                    f'   • {child.name}: {child.available_child_stock} units '
                    f'(min: {child.min_stock_level})'
                )
            if len(low_stock_children) > 5:
                self.stdout.write(f'   ... and {len(low_stock_children) - 5} more')
        
        self.stdout.write('')