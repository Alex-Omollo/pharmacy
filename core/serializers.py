from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from decimal import Decimal
from .models import (
    User, Role, Supplier,
    Product, Category, StockMovement,
    Sale, SaleItem, Payment, StockAlert,
    PurchaseOrder, PurchaseOrderItem,
    Medicine, Batch, StockReceiving, StockReceivingItem,
    MedicineStockMovement, PharmacySale, PharmacySaleItem,
    ControlledDrugRegister, Store
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class StoreSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Store
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'address', 'phone', 'email', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class StoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'name', 'description', 'is_default', 'is_active',
            'address', 'phone', 'email', 'business_registration', 'tax_id'
        ]
    
    def validate(self, attrs):
        # If setting as default, ensure user is admin
        if attrs.get('is_default', False):
            if not self.context['request'].user.is_admin:
                raise serializers.ValidationError(
                    "Only admins can set a store as default"
                )
        return attrs

class StoreSetupSerializer(serializers.Serializer):
    """Serializer for initial store setup"""
    name = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    business_registration = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tax_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Store name cannot be empty")
        return value.strip()
    
class CompleteSetupSerializer(serializers.Serializer):
    """Serializer for completing initial setup"""
    store = StoreSetupSerializer(required=True)
    
    # Optional: Admin can update their profile during setup
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    
    def create(self, validated_data):
        from django.db import transaction
        
        user = self.context['request'].user
        store_data = validated_data.pop('store')
        
        with transaction.atomic():
            # Create the store
            store = Store.create_initial_store(
                name=store_data['name'],
                admin_user=user,
                description=store_data.get('description', ''),
                address=store_data.get('address', ''),
                phone=store_data.get('phone', ''),
                email=store_data.get('email', ''),
                business_registration=store_data.get('business_registration', ''),
                tax_id=store_data.get('tax_id', '')
            )
            
            # Assign store to admin user
            user.store = store
            user.has_completed_setup = True
            
            # Update admin profile if provided
            if validated_data.get('first_name'):
                user.first_name = validated_data['first_name']
            if validated_data.get('last_name'):
                user.last_name = validated_data['last_name']
            if validated_data.get('phone'):
                user.phone = validated_data['phone']
            
            user.save()
        
        return {'store': store, 'user': user}

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display = serializers.CharField(source='role.get_name_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'address', 'role', 'role_name', 'role_display',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone', 'address', 'role'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name',
            'phone', 'address', 'role', 'is_active'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    

##
class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    available_stock = serializers.SerializerMethodField()
    display_stock = serializers.CharField(read_only=True)
    parent_name = serializers.CharField(source='parent_product.name', read_only=True, allow_null=True)
    stock_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'category', 'category_name',
            'product_type', 'parent_product', 'parent_name',
            'base_unit', 'unit_quantity', 'conversion_factor',
            'price', 'stock_quantity', 'available_stock', 'display_stock',
            'is_low_stock', 'is_active', 'image'
        ]
    
    def get_available_stock(self, obj):
        """Get available stock considering parent-child relationship"""
        return obj.available_child_stock
    
    def get_stock_quantity(self, obj):
        """Return actual stock for display purposes"""
        if obj.product_type == 'child':
            # For child products, return available stock instead of stored 0
            return obj.available_child_stock
        return obj.stock_quantity


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    price_with_tax = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit_margin = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    available_stock = serializers.SerializerMethodField()
    display_stock = serializers.CharField(read_only=True)
    parent_name = serializers.CharField(source='parent_product.name', read_only=True)
    child_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'category', 'category_name',
            'description', 'price', 'cost_price', 'tax_rate', 'price_with_tax',
            'product_type', 'parent_product', 'parent_name', 'child_products',
            'base_unit', 'unit_quantity', 'conversion_factor',
            'stock_quantity', 'available_stock', 'display_stock',
            'min_stock_level', 'is_low_stock', 'profit_margin',
            'is_active', 'image', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_available_stock(self, obj):
        """Get available stock considering parent-child relationship"""
        return obj.available_child_stock
    
    def get_child_products(self, obj):
        """Get list of child products if this is a parent"""
        if obj.product_type == 'parent':
            children = obj.child_products.filter(is_active=True)
            return [{
                'id': child.id,
                'name': child.name,
                'sku': child.sku,
                'unit_quantity': str(child.unit_quantity),
                'base_unit': child.base_unit,
                'price': str(child.price),
                'available_stock': child.available_child_stock
            } for child in children]
        return []


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    sku = serializers.CharField(required=False, allow_blank=True)
    barcode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'category', 'description',
            'product_type', 'parent_product', 'base_unit', 'unit_quantity',
            'conversion_factor', 'price', 'cost_price', 'tax_rate',
            'stock_quantity', 'min_stock_level', 'is_active', 'image'
        ]
    
    def validate(self, attrs):
        """Additional validation"""
        product_type = attrs.get('product_type', 'simple')
        parent_product = attrs.get('parent_product')
        
        # Validate parent-child relationship
        if product_type == 'child' and not parent_product:
            raise serializers.ValidationError({
                "parent_product": "Child products must have a parent product."
            })
        
        if product_type == 'parent' and parent_product:
            raise serializers.ValidationError({
                "parent_product": "Parent products cannot have a parent."
            })
        
        if product_type == 'simple' and parent_product:
            raise serializers.ValidationError({
                "parent_product": "Simple products cannot have a parent."
            })
        
        # Validate pricing
        price = attrs.get('price')
        cost_price = attrs.get('cost_price')
        if price and cost_price and price < cost_price:
            raise serializers.ValidationError({
                "price": "Selling price cannot be less than cost price."
            })
        
        # Validate child product stock (should be 0 for child products)
        if product_type == 'child':
            attrs['stock_quantity'] = 0  # Child stock is calculated from parent
        
        return attrs
    
    def validate_sku(self, value):
        """Ensure SKU is unique"""
        if not value:
            return value
            
        instance = self.instance
        if instance and instance.sku == value:
            return value
        
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate_barcode(self, value):
        """Ensure barcode is unique if provided"""
        # Allow empty or None barcode
        if not value:
            return None
        
        instance = self.instance
        if instance and instance.barcode == value:
            return value
        
        if Product.objects.filter(barcode=value).exists():
            raise serializers.ValidationError("Product with this barcode already exists.")
        return value


class ChildProductCreateSerializer(serializers.Serializer):
    """Serializer for creating child products from parent"""
    parent_id = serializers.IntegerField()
    child_products = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate_parent_id(self, value):
        try:
            product = Product.objects.get(id=value)
            if product.product_type != 'parent':
                raise serializers.ValidationError("Product must be a parent product.")
        except Product.DoesNotExist:
            raise serializers.ValidationError("Parent product not found.")
        return value
    
    def validate_child_products(self, value):
        """Validate child product data - name is optional and auto-generated"""
        if not value:
            raise serializers.ValidationError("At least one child product is required.")
        
        for idx, child in enumerate(value):
            # Only unit_quantity and price are required
            # Name will be auto-generated from parent name + unit_quantity
            if 'unit_quantity' not in child or not child['unit_quantity']:
                raise serializers.ValidationError(f"Child product {idx + 1}: unit_quantity is required")
            
            if 'price' not in child or not child['price']:
                raise serializers.ValidationError(f"Child product {idx + 1}: price is required")
            
            # Validate unit_quantity is positive
            try:
                qty = float(child['unit_quantity'])
                if qty <= 0:
                    raise serializers.ValidationError(f"Child product {idx + 1}: unit_quantity must be positive")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Child product {idx + 1}: Invalid unit_quantity")
            
            # Validate price is positive
            try:
                price_val = float(child['price'])
                if price_val <= 0:
                    raise serializers.ValidationError(f"Child product {idx + 1}: price must be positive")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Child product {idx + 1}: Invalid price")
        
        return value


class BulkProductUploadSerializer(serializers.Serializer):
    """Serializer for bulk product upload via CSV"""
    csv_file = serializers.FileField()
    
    def validate_csv_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("Only CSV files are allowed.")
        return value
    
## 
class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'tax_rate', 'discount_percent', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'payment_method', 'amount', 'reference_number', 'notes']
        read_only_fields = ['id']


class SaleListSerializer(serializers.ModelSerializer):
    """Serializer for sale list view"""
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'cashier', 'cashier_name',
            'customer_name', 'total', 'payment_method', 'status',
            'items_count', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class SaleDetailSerializer(serializers.ModelSerializer):
    """Serializer for sale detail view"""
    items = SaleItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'invoice_number', 'cashier', 'cashier_name',
            'customer_name', 'subtotal', 'tax_amount', 'discount_amount',
            'total', 'payment_method', 'amount_paid', 'change_amount',
            'status', 'notes', 'items', 'payments', 'created_at', 'updated_at'
        ]


class SaleItemCreateSerializer(serializers.Serializer):
    """Serializer for creating sale items"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    discount_percent = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        min_value=0,
        max_value=100
    )


class SaleCreateSerializer(serializers.Serializer):
    """Serializer for creating a sale with bulk product support"""
    customer_name = serializers.CharField(required=False, allow_blank=True)
    items = SaleItemCreateSerializer(many=True)
    payment_method = serializers.ChoiceField(
        choices=['cash', 'card', 'mobile'],
        default='cash'
    )
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
    
    def validate(self, attrs):
        # Validate customer name for mobile payments
        payment_method = attrs.get('payment_method')
        customer_name = attrs.get('customer_name', '').strip()
        
        # Require customer name for mobile payments
        if payment_method == 'mobile' and not customer_name:
            raise serializers.ValidationError({
                "customer_name": "Customer name is required for M-Pesa payments."
            })
        
        # Calculate totals
        items_data = attrs.get('items', [])
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        discount_amount = Decimal('0.00')
        
        for item_data in items_data:
            try:
                product = Product.objects.get(id=item_data['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(
                    f"Product with id {item_data['product_id']} not found."
                )
            
            # Check stock availability based on product type
            quantity_requested = item_data['quantity']
            
            if product.product_type == 'child':
                # For child products, check available stock from parent
                if not product.can_sell(quantity_requested):
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.available_child_stock}, "
                        f"Requested: {quantity_requested}"
                    )
            elif product.product_type == 'parent':
                # Allow selling parent products directly
                if product.stock_quantity < quantity_requested:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock_quantity}, "
                        f"Requested: {quantity_requested}"
                    )
            else:  # simple
                if product.stock_quantity < quantity_requested:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock_quantity}"
                    )
            
            # Calculate amounts with proper Decimal precision
            quantity = Decimal(str(item_data['quantity']))
            unit_price = Decimal(str(product.price))
            discount_percent = Decimal(str(item_data.get('discount_percent', 0)))
            tax_rate = Decimal(str(product.tax_rate))
            
            # Calculate step by step
            item_subtotal = unit_price * quantity
            item_discount = item_subtotal * (discount_percent / Decimal('100'))
            item_after_discount = item_subtotal - item_discount
            item_tax = item_after_discount * (tax_rate / Decimal('100'))
            
            subtotal += item_subtotal
            discount_amount += item_discount
            tax_amount += item_tax
        
        total = subtotal - discount_amount + tax_amount
        
        # Round to 2 decimal places
        total = total.quantize(Decimal('0.01'))
        
        # Validate payment amount
        amount_paid = Decimal(str(attrs['amount_paid']))
        
        if amount_paid < total:
            raise serializers.ValidationError(
                f"Amount paid (ksh {amount_paid}) is less than total (ksh {total})."
            )
        
        # Store calculated values
        attrs['_calculated'] = {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'tax_amount': tax_amount.quantize(Decimal('0.01')),
            'discount_amount': discount_amount.quantize(Decimal('0.01')),
            'total': total,
            'change_amount': (amount_paid - total).quantize(Decimal('0.01'))
        }
    
        return attrs
    
    def create(self, validated_data):
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        calculated = validated_data.pop('_calculated')
        
        with transaction.atomic():
            # Create sale
            sale = Sale.objects.create(
                cashier=self.context['request'].user,
                customer_name=validated_data.get('customer_name', ''),
                subtotal=calculated['subtotal'],
                tax_amount=calculated['tax_amount'],
                discount_amount=calculated['discount_amount'],
                total=calculated['total'],
                payment_method=validated_data['payment_method'],
                amount_paid=validated_data['amount_paid'],
                change_amount=calculated['change_amount'],
                notes=validated_data.get('notes', ''),
                status='completed'
            )
            
            # Create sale items and update stock
            for item_data in items_data:
                product = Product.objects.select_for_update().get(id=item_data['product_id'])
                quantity_sold = item_data['quantity']
                
                # Create sale item
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    quantity=quantity_sold,
                    unit_price=product.price,
                    tax_rate=product.tax_rate,
                    discount_percent=item_data.get('discount_percent', 0)
                )
                
                # Update stock based on product type
                if product.product_type == 'child':
                    # Update parent stock
                    previous_parent_stock = product.parent_product.stock_quantity
                    parent_units_consumed = product.update_parent_stock(quantity_sold)
                    
                    # Create stock movement for parent
                    StockMovement.objects.create(
                        product=product.parent_product,
                        movement_type='sale',
                        quantity=-int(parent_units_consumed),
                        previous_quantity=previous_parent_stock,
                        new_quantity=product.parent_product.stock_quantity,
                        sale=sale,
                        user=self.context['request'].user,
                        notes=f'Sold {quantity_sold} x {product.name}'
                    )
                    
                    # Also create movement for child (for tracking)
                    StockMovement.objects.create(
                        product=product,
                        movement_type='sale',
                        quantity=-quantity_sold,
                        previous_quantity=int(product.available_child_stock + quantity_sold),
                        new_quantity=int(product.available_child_stock),
                        sale=sale,
                        user=self.context['request'].user,
                        notes=f"Sold {quantity_sold} x {product.name} (reduced parent stock by {parent_units_consumed} units)"
                    )
                    
                elif product.product_type == 'parent':
                    # Direct parent sale (selling bulk items)
                    previous_stock = product.stock_quantity
                    product.stock_quantity -= quantity_sold
                    product.save()
                    
                    StockMovement.objects.create(
                        product=product,
                        movement_type='sale',
                        quantity=-quantity_sold,
                        previous_quantity=previous_stock,
                        new_quantity=product.stock_quantity,
                        sale=sale,
                        user=self.context['request'].user
                    )
                    
                else:  # simple product
                    previous_stock = product.stock_quantity
                    product.stock_quantity -= quantity_sold
                    product.save()
                    
                    StockMovement.objects.create(
                        product=product,
                        movement_type='sale',
                        quantity=-quantity_sold,
                        previous_quantity=previous_stock,
                        new_quantity=product.stock_quantity,
                        sale=sale,
                        user=self.context['request'].user
                    )
            
            # Create payment record
            Payment.objects.create(
                sale=sale,
                payment_method=validated_data['payment_method'],
                amount=validated_data['amount_paid']
            )
        
        return sale
    
## 
class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ['created_at', 'updated_at', 'store']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'movement_type', 'movement_type_display', 'quantity',
            'previous_quantity', 'new_quantity', 'unit_cost',
            'reference_number', 'supplier', 'supplier_name',
            'sale', 'user', 'user_name', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for manual stock adjustments"""
    product_id = serializers.IntegerField()
    adjustment_type = serializers.ChoiceField(choices=['add', 'remove', 'set'])
    quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=500)
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, attrs):
        try:
            product = Product.objects.get(id=attrs['product_id'])
        except Product.DoesNotExist:
            raise serializers.ValidationError(f"Product with id {attrs['product_id']} not found.")
        
        adjustment_type = attrs['adjustment_type']
        quantity = attrs['quantity']
        
        if adjustment_type == 'remove' and product.stock_quantity < quantity:
            raise serializers.ValidationError(
                f"Cannot remove {quantity} units. Only {product.stock_quantity} available."
            )
        
        attrs['_product'] = product
        return attrs


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity_ordered', 'quantity_received', 'unit_cost', 'subtotal'
        ]
        read_only_fields = ['subtotal']


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    items_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name',
            'order_date', 'expected_delivery_date', 'status', 'status_display',
            'total', 'items_count', 'created_by_name', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_name',
            'order_date', 'expected_delivery_date', 'received_date',
            'status', 'status_display', 'subtotal', 'tax_amount', 'total',
            'notes', 'items', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    items = serializers.ListField(child=serializers.DictField())
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_supplier_id(self, value):
        try:
            Supplier.objects.get(id=value)
        except Supplier.DoesNotExist:
            raise serializers.ValidationError(f"Supplier with id {value} not found.")
        return value
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        
        for item in value:
            if 'product_id' not in item or 'quantity' not in item or 'unit_cost' not in item:
                raise serializers.ValidationError(
                    "Each item must have product_id, quantity, and unit_cost."
                )
        
        return value
    
    def create(self, validated_data):
        from django.db import transaction
        from decimal import Decimal
        
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Create purchase order
            po = PurchaseOrder.objects.create(
                supplier_id=validated_data['supplier_id'],
                expected_delivery_date=validated_data.get('expected_delivery_date'),
                notes=validated_data.get('notes', ''),
                created_by=self.context['request'].user,
                status='pending'
            )
            
            # Create items and calculate totals
            subtotal = Decimal('0.00')
            
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = int(item_data['quantity'])
                unit_cost = Decimal(str(item_data['unit_cost']))
                
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity_ordered=quantity,
                    unit_cost=unit_cost
                )
                
                subtotal += unit_cost * quantity
            
            # Update PO totals
            po.subtotal = subtotal
            # po.tax_amount = subtotal * Decimal('0.16')  # 16% tax
            po.total = po.subtotal # po.subtotal + po.tax_amount
            po.save()
        
        return po


class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = StockAlert
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'alert_level', 'current_stock', 'is_resolved',
            'resolved_at', 'created_at'
        ]
        
# class ChildProductCreateSerializer(serializers.Serializer):
#     """Serializer for creating child products from parent"""
#     parent_id = serializers.IntegerField()
#     child_products = serializers.ListField(
#         child=serializers.DictField()
#     )
    
#     def validate_parent_id(self, value):
#         try:
#             product = Product.objects.get(id=value)
#             if product.product_type != 'parent':
#                 raise serializers.ValidationError("Product must be a parent product.")
#         except Product.DoesNotExist:
#             raise serializers.ValidationError("Parent product not found.")
#         return value
    
#     def validate_child_products(self, value):
#         """Validate child product data"""
#         if not value:
#             raise serializers.ValidationError("At least one child product is required.")
        
#         for child in value:
#             required_fields = ['name', 'unit_quantity', 'price']
#             for field in required_fields:
#                 if field not in child:
#                     raise serializers.ValidationError(f"Missing required field: {field}")
            
#             # Validate unit_quantity is positive
#             try:
#                 qty = float(child['unit_quantity'])
#                 if qty <= 0:
#                     raise serializers.ValidationError("unit_quantity must be positive")
#             except (ValueError, TypeError):
#                 raise serializers.ValidationError("Invalid unit_quantity")
        
#         return value

# =================================
# Medicine serializer
# =================================

class  MedicineListSerializer(serializers.ModelSerializer):
    """List view for medicines"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    active_batches_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'sku', 'barcode',
            'category', 'category_name', 'schedule', 'dosage_form',
            'strength', 'manufacturer', 'default_selling_price',
            'total_stock', 'is_low_stock', 'active_batches_count',
            'is_active', 'created_at'
        ]
    
    def get_active_batches_count(self, obj):
        return obj.batches.filter(is_expired=False, quantity__gt=0).count()


class MedicineDetailSerializer(serializers.ModelSerializer):
    """Detail view for medicines with batches"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    requires_prescription = serializers.BooleanField(read_only=True)
    is_controlled_drug = serializers.BooleanField(read_only=True)
    batches = serializers.SerializerMethodField()
    
    class Meta:
        model = Medicine
        fields = [
            'id', 'name', 'generic_name', 'medicine_type', 'sku', 'barcode',
            'category', 'category_name', 'schedule', 'dosage_form', 'strength',
            'manufacturer', 'description', 'default_selling_price',
            'storage_instructions', 'contraindications', 'side_effects',
            'min_stock_level', 'reorder_level', 'total_stock', 'is_low_stock',
            'requires_prescription', 'is_controlled_drug', 'is_active',
            'batches', 'created_at', 'updated_at'
        ]
    
    def get_batches(self, obj):
        """Get active batches for this medicine"""
        batches = obj.batches.filter(quantity__gt=0).order_by('expiry_date')
        return BatchListSerializer(batches, many=True).data


class MedicineCreateUpdateSerializer(serializers.ModelSerializer):
    """Create/Update medicine"""
    sku = serializers.CharField(required=False, allow_blank=True)
    barcode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = Medicine
        fields = [
            'name', 'generic_name', 'medicine_type', 'sku', 'barcode',
            'category', 'schedule', 'dosage_form', 'strength', 'manufacturer',
            'description', 'price', 'cost_price', 'storage_instructions',
            'contraindications', 'side_effects', 'min_stock_level',
            'reorder_level', 'is_active'
        ]
    
    def validate_sku(self, value):
        if not value:
            return value
        instance = self.instance
        if instance and instance.sku == value:
            return value
        if Medicine.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Medicine with this SKU already exists.")
        return value


# ============================================================================
# BATCH SERIALIZERS
# ============================================================================

class BatchListSerializer(serializers.ModelSerializer):
    """List view for batches"""
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    status = serializers.CharField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    can_dispense = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Batch
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number',
            'expiry_date', 'quantity', 'selling_price', 'purchase_price',
            'status', 'days_to_expiry', 'can_dispense', 'is_blocked',
            'received_date'
        ]


class BatchDetailSerializer(serializers.ModelSerializer):
    """Detail view for batch"""
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)
    status = serializers.CharField(read_only=True)
    days_to_expiry = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_near_expiry = serializers.SerializerMethodField()
    can_dispense = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Batch
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number', 'supplier',
            'supplier_name', 'manufacture_date', 'expiry_date', 'received_date',
            'quantity', 'initial_quantity', 'purchase_price', 'selling_price',
            'status', 'days_to_expiry', 'is_expired', 'is_near_expiry',
            'can_dispense', 'is_blocked', 'block_reason', 'received_by',
            'received_by_name', 'created_at', 'updated_at'
        ]
    
    def get_is_near_expiry(self, obj):
        return obj.is_near_expiry()


class BatchCreateSerializer(serializers.ModelSerializer):
    """Create new batch (usually via stock receiving)"""
    
    class Meta:
        model = Batch
        fields = [
            'medicine', 'batch_number', 'supplier', 'manufacture_date',
            'expiry_date', 'initial_quantity', 'quantity', 'purchase_price',
            'selling_price'
        ]
    
    def validate(self, attrs):
        # Ensure expiry date is in the future
        if attrs['expiry_date'] <= timezone.now().date():
            raise serializers.ValidationError({
                "expiry_date": "Expiry date must be in the future."
            })
        
        # Initial quantity should match quantity for new batches
        if 'initial_quantity' in attrs and 'quantity' in attrs:
            if attrs['initial_quantity'] != attrs['quantity']:
                attrs['quantity'] = attrs['initial_quantity']
        
        return attrs


class BatchUpdateSerializer(serializers.ModelSerializer):
    """Update batch (mainly selling price and blocking)"""
    
    class Meta:
        model = Batch
        fields = ['selling_price', 'is_blocked', 'block_reason']


# ============================================================================
# STOCK RECEIVING SERIALIZERS
# ============================================================================

class StockReceivingItemSerializer(serializers.ModelSerializer):
    """Stock receiving item serializer"""
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    
    class Meta:
        model = StockReceivingItem
        fields = [
            'id', 'medicine', 'medicine_name', 'batch_number', 'expiry_date',
            'manufacture_date', 'quantity_received', 'purchase_price',
            'selling_price', 'line_cost'
        ]
        read_only_fields = ['line_cost']


class StockReceivingListSerializer(serializers.ModelSerializer):
    """List view for stock receivings"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)
    
    class Meta:
        model = StockReceiving
        fields = [
            'id', 'receiving_number', 'supplier', 'supplier_name',
            'supplier_invoice_number', 'invoice_date', 'total_items',
            'total_cost', 'status', 'received_by_name', 'received_date'
        ]


class StockReceivingDetailSerializer(serializers.ModelSerializer):
    """Detail view for stock receiving"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)
    items = StockReceivingItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = StockReceiving
        fields = [
            'id', 'receiving_number', 'supplier', 'supplier_name',
            'supplier_invoice_number', 'invoice_date', 'total_items',
            'total_cost', 'status', 'notes', 'items', 'received_by',
            'received_by_name', 'received_date', 'completed_date'
        ]


class StockReceivingCreateSerializer(serializers.Serializer):
    """Create stock receiving with items"""
    supplier_id = serializers.IntegerField()
    supplier_invoice_number = serializers.CharField(required=False, allow_blank=True)
    invoice_date = serializers.DateField(required=False, allow_null=True)
    items = serializers.ListField(child=serializers.DictField())
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        
        for item in value:
            required = ['medicine_id', 'batch_number', 'expiry_date', 'quantity_received', 'purchase_price', 'selling_price']
            for field in required:
                if field not in item:
                    raise serializers.ValidationError(f"Missing required field: {field}")
        
        return value
    
    def create(self, validated_data):
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Create receiving record
            receiving = StockReceiving.objects.create(
                supplier_id=validated_data['supplier_id'],
                supplier_invoice_number=validated_data.get('supplier_invoice_number', ''),
                invoice_date=validated_data.get('invoice_date'),
                notes=validated_data.get('notes', ''),
                received_by=self.context['request'].user,
                status='completed'
            )
            
            total_cost = Decimal('0.00')
            
            for item_data in items_data:
                medicine = Medicine.objects.get(id=item_data['medicine_id'])
                
                # Create or update batch
                batch, created = Batch.objects.get_or_create(
                    medicine=medicine,
                    batch_number=item_data['batch_number'],
                    defaults={
                        'supplier_id': validated_data['supplier_id'],
                        'expiry_date': item_data['expiry_date'],
                        'manufacture_date': item_data.get('manufacture_date'),
                        'initial_quantity': item_data['quantity_received'],
                        'quantity': item_data['quantity_received'],
                        'purchase_price': item_data['purchase_price'],
                        'selling_price': item_data['selling_price'],
                        'received_by': self.context['request'].user
                    }
                )
                
                if not created:
                    # Update existing batch quantity
                    batch.quantity += item_data['quantity_received']
                    batch.save()
                
                # Create receiving item
                receiving_item = StockReceivingItem.objects.create(
                    receiving=receiving,
                    medicine=medicine,
                    batch=batch,
                    batch_number=item_data['batch_number'],
                    expiry_date=item_data['expiry_date'],
                    manufacture_date=item_data.get('manufacture_date'),
                    quantity_received=item_data['quantity_received'],
                    purchase_price=item_data['purchase_price'],
                    selling_price=item_data['selling_price']
                )
                
                total_cost += receiving_item.line_cost
                
                # Create stock movement
                MedicineStockMovement.objects.create(
                    medicine=medicine,
                    batch=batch,
                    movement_type='receiving',
                    quantity=item_data['quantity_received'],
                    previous_quantity=batch.quantity - item_data['quantity_received'],
                    new_quantity=batch.quantity,
                    reference_number=receiving.receiving_number,
                    receiving=receiving,
                    performed_by=self.context['request'].user
                )
                
                # If controlled drug, create register entry
                if medicine.is_controlled_drug:
                    ControlledDrugRegister.objects.create(
                        medicine=medicine,
                        batch=batch,
                        transaction_type='receiving',
                        quantity=item_data['quantity_received'],
                        balance=batch.quantity,
                        receiving=receiving,
                        dispensed_by=self.context['request'].user
                    )
            
            # Update receiving totals
            receiving.total_items = len(items_data)
            receiving.total_cost = total_cost
            receiving.completed_date = timezone.now()
            receiving.save()
        
        return receiving


# ============================================================================
# PHARMACY SALE SERIALIZERS
# ============================================================================

class PharmacySaleItemSerializer(serializers.ModelSerializer):
    """Pharmacy sale item"""
    
    class Meta:
        model = PharmacySaleItem
        fields = [
            'id', 'medicine', 'medicine_name', 'batch', 'batch_number',
            'expiry_date', 'quantity', 'unit_price', 'discount_percent',
            'subtotal', 'requires_prescription', 'prescription_verified'
        ]
        read_only_fields = ['subtotal']


class PharmacySaleListSerializer(serializers.ModelSerializer):
    """List view for pharmacy sales"""
    dispenser_name = serializers.CharField(source='dispenser.username', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PharmacySale
        fields = [
            'id', 'invoice_number', 'customer_name', 'dispenser',
            'dispenser_name', 'total', 'payment_method', 'status',
            'has_prescription', 'items_count', 'created_at'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class PharmacySaleDetailSerializer(serializers.ModelSerializer):
    """Detail view for pharmacy sale"""
    dispenser_name = serializers.CharField(source='dispenser.username', read_only=True)
    voided_by_name = serializers.CharField(source='voided_by.username', read_only=True)
    items = PharmacySaleItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PharmacySale
        fields = [
            'id', 'invoice_number', 'customer_name', 'customer_phone',
            'has_prescription', 'prescription_number', 'prescriber_name',
            'dispenser', 'dispenser_name', 'subtotal', 'discount_amount',
            'tax_amount', 'total', 'payment_method', 'amount_paid',
            'change_amount', 'status', 'voided_by', 'voided_by_name',
            'voided_at', 'void_reason', 'notes', 'items',
            'created_at', 'updated_at'
        ]


class PharmacySaleItemCreateSerializer(serializers.Serializer):
    """Create pharmacy sale item"""
    medicine_id = serializers.IntegerField()
    batch_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=0, min_value=0, max_value=100)
    prescription_verified = serializers.BooleanField(default=False)


class PharmacySaleCreateSerializer(serializers.Serializer):
    """Create pharmacy sale with FEFO batch selection"""
    customer_name = serializers.CharField(required=False, allow_blank=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True)
    has_prescription = serializers.BooleanField(default=False)
    prescription_number = serializers.CharField(required=False, allow_blank=True)
    prescriber_name = serializers.CharField(required=False, allow_blank=True)
    items = PharmacySaleItemCreateSerializer(many=True)
    payment_method = serializers.ChoiceField(choices=['cash', 'card', 'mobile', 'insurance'], default='cash')
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value
    
    def validate(self, attrs):
        """Validate sale and calculate totals"""
        items_data = attrs.get('items', [])
        subtotal = Decimal('0.00')
        discount_amount = Decimal('0.00')
        
        for item_data in items_data:
            try:
                medicine = Medicine.objects.get(id=item_data['medicine_id'])
            except Medicine.DoesNotExist:
                raise serializers.ValidationError(f"Medicine with id {item_data['medicine_id']} not found.")
            
            # Check if prescription is required
            if medicine.requires_prescription and not item_data.get('prescription_verified'):
                if not attrs.get('has_prescription'):
                    raise serializers.ValidationError(
                        f"{medicine.name} requires a prescription but none was provided."
                    )
            
            # Get or select batch (FEFO)
            if item_data.get('batch_id'):
                try:
                    batch = Batch.objects.get(id=item_data['batch_id'], medicine=medicine)
                except Batch.DoesNotExist:
                    raise serializers.ValidationError(f"Batch not found for {medicine.name}")
            else:
                # Auto-select using FEFO (First Expiry, First Out)
                batch = Batch.objects.filter(
                    medicine=medicine,
                    is_expired=False,
                    is_blocked=False,
                    quantity__gte=item_data['quantity']
                ).order_by('expiry_date').first()
                
                if not batch:
                    raise serializers.ValidationError(
                        f"No available batch for {medicine.name}. Required: {item_data['quantity']}"
                    )
                
                item_data['batch_id'] = batch.id
            
            # Check stock availability
            if batch.quantity < item_data['quantity']:
                raise serializers.ValidationError(
                    f"Insufficient stock in batch {batch.batch_number} for {medicine.name}. "
                    f"Available: {batch.quantity}, Required: {item_data['quantity']}"
                )
            
            # Warn on near expiry
            if batch.is_near_expiry(30):  # 30 days warning
                item_data['_near_expiry_warning'] = f"Batch {batch.batch_number} expires in {batch.days_to_expiry} days"
            
            # Calculate amounts
            quantity = Decimal(str(item_data['quantity']))
            unit_price = batch.selling_price
            discount_percent = Decimal(str(item_data.get('discount_percent', 0)))
            
            item_subtotal = unit_price * quantity
            item_discount = item_subtotal * (discount_percent / Decimal('100'))
            
            subtotal += item_subtotal
            discount_amount += item_discount
            
            # Store calculated values
            item_data['_batch'] = batch
            item_data['_unit_price'] = unit_price
        
        total = subtotal - discount_amount
        total = total.quantize(Decimal('0.01'))
        
        # Validate payment
        amount_paid = Decimal(str(attrs['amount_paid']))
        if amount_paid < total:
            raise serializers.ValidationError(
                f"Amount paid (KES {amount_paid}) is less than total (KES {total})."
            )
        
        attrs['_calculated'] = {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'discount_amount': discount_amount.quantize(Decimal('0.01')),
            'tax_amount': Decimal('0.00'),
            'total': total,
            'change_amount': (amount_paid - total).quantize(Decimal('0.01'))
        }
        
        return attrs
    
    def create(self, validated_data):
        from django.db import transaction
        
        items_data = validated_data.pop('items')
        calculated = validated_data.pop('_calculated')
        
        with transaction.atomic():
            # Create sale
            sale = PharmacySale.objects.create(
                customer_name=validated_data.get('customer_name', ''),
                customer_phone=validated_data.get('customer_phone', ''),
                has_prescription=validated_data.get('has_prescription', False),
                prescription_number=validated_data.get('prescription_number', ''),
                prescriber_name=validated_data.get('prescriber_name', ''),
                dispenser=self.context['request'].user,
                subtotal=calculated['subtotal'],
                discount_amount=calculated['discount_amount'],
                tax_amount=calculated['tax_amount'],
                total=calculated['total'],
                payment_method=validated_data['payment_method'],
                amount_paid=validated_data['amount_paid'],
                change_amount=calculated['change_amount'],
                notes=validated_data.get('notes', ''),
                status='completed'
            )
            
            # Create sale items and update stock
            for item_data in items_data:
                batch = item_data['_batch']
                medicine = batch.medicine
                quantity = item_data['quantity']
                
                # Create sale item
                PharmacySaleItem.objects.create(
                    sale=sale,
                    medicine=medicine,
                    batch=batch,
                    medicine_name=medicine.name,
                    batch_number=batch.batch_number,
                    expiry_date=batch.expiry_date,
                    quantity=quantity,
                    unit_price=item_data['_unit_price'],
                    discount_percent=item_data.get('discount_percent', 0),
                    requires_prescription=medicine.requires_prescription,
                    prescription_verified=item_data.get('prescription_verified', False)
                )
                
                # Update batch stock
                previous_quantity = batch.quantity
                batch.quantity -= quantity
                batch.save()
                
                # Create stock movement
                MedicineStockMovement.objects.create(
                    medicine=medicine,
                    batch=batch,
                    movement_type='sale',
                    quantity=-quantity,
                    previous_quantity=previous_quantity,
                    new_quantity=batch.quantity,
                    reference_number=sale.invoice_number,
                    sale=sale,
                    performed_by=self.context['request'].user
                )
                
                # If controlled drug, create register entry
                if medicine.is_controlled_drug:
                    ControlledDrugRegister.objects.create(
                        medicine=medicine,
                        batch=batch,
                        transaction_type='dispensing',
                        quantity=quantity,
                        balance=batch.quantity,
                        customer_name=sale.customer_name,
                        prescription_number=sale.prescription_number,
                        prescriber_name=sale.prescriber_name,
                        sale=sale,
                        dispensed_by=self.context['request'].user
                    )
        
        return sale


# ============================================================================
# STOCK MOVEMENT SERIALIZERS
# ============================================================================

class MedicineStockMovementSerializer(serializers.ModelSerializer):
    """Medicine stock movement"""
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    batch_number = serializers.CharField(source='batch.batch_number', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)
    
    class Meta:
        model = MedicineStockMovement
        fields = [
            'id', 'medicine', 'medicine_name', 'batch', 'batch_number',
            'movement_type', 'quantity', 'previous_quantity', 'new_quantity',
            'reference_number', 'reason', 'performed_by', 'performed_by_name',
            'created_at'
        ]