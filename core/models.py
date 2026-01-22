from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Store(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(
        default=False,
        help_text='Mark this as the default store',
    )
    is_active = models.BooleanField(
        default=True, 
        help_text='Whether this store is active',
    )
    address = models.TextField(blank=True)
    phone = models.CharField(blank=True, max_length=20)
    email = models.EmailField(blank=True)
    business_registration = models.CharField(max_length=100, blank=True, help_text='Business registration number')
    tax_id = models.CharField(max_length=100, blank=True, help_text='Tax ID/VAT number')
    created_by = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_stores'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stores'
        ordering = ['-is_default', 'name']
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        
        
    def __str__(self):
        return f"{self.name}{' (default)' if self.is_default else ''}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Store.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_store(cls):
        """Get the default store"""
        return cls.objects.filter(is_default=True, is_active=True).first()
        
        # """Get the default store, create one if none exists"""
        # default_store = cls.objects.filter(is_default=True).first()
        # if not default_store:
            
        #     admin_user = User.objects.filter(role__name='admin').first()
            
        #     default_store = cls.objects.create(
        #         name='Default Store',
        #         description='Default store for the system',
        #         is_default=True,
        #         is_active=True,
        #         created_by=User.objects.get(username='admin')
        #     )
        # return default_store
    
    @classmethod
    def setup_required(cls):
        """Check if initial store setup is required"""
        return not cls.objects.exists()
    
    @classmethod
    def create_initial_store(cls, name, admin_user, **kwargs):
        """Create the first store during setup"""
        return cls.objects.create(
            name=name,
            is_default=True,
            is_active=True,
            created_by=admin_user,
            **kwargs
        )

class StoreFilteredManager(models.Manager):
    """Manager that filters by store"""
    
    def for_store(self, store):
        return self.filter(store=store)
    
    
class Role(models.Model):
    """User roles for POS system"""
    ADMIN = 'admin'
    MANAGER = 'manager'
    CASHIER = 'cashier'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (CASHIER, 'Cashier'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.get_name_display()
    
    class Meta:
        db_table = 'roles'


class User(AbstractUser):
    """Custom user model with role-based access"""
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='users'
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    has_completed_setup = models.BooleanField(
        default=False,
        help_text='Whether the user has completed initial setup'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role.name if self.role else 'No Role'})"
    
    @property
    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN
    
    @property
    def is_manager(self):
        return self.role and self.role.name == Role.MANAGER
    
    @property
    def is_cashier(self):
        return self.role and self.role.name == Role.CASHIER
    
    class Meta:
        db_table = 'users'
        
##
class Category(models.Model):
    """Product categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    objects = StoreFilteredManager()
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = [['name', 'store']]


class Product(models.Model):
    """Product catalog with bulk tracking support"""
    
    # Product Types
    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple Product'),
        ('parent', 'Bulk/Parent Product'),
        ('child', 'Child Product'),
    ]
    
    # Base unit choices for standardization
    UNIT_CHOICES = [
        ('g', 'Grams'),
        ('kg', 'Kilograms'),
        ('ml', 'Milliliters'),
        ('l', 'Liters'),
        ('pcs', 'Pieces'),
        ('box', 'Box'),
        ('pack', 'Pack'),
    ]
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products'
    )
    description = models.TextField(blank=True)
    
    # Product type and parent-child relationship
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='simple',
        help_text="Simple=standalone, Parent=bulk item, Child=derived from parent"
    )
    parent_product = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='child_products',
        help_text="Parent product for child items"
    )
    
    # Unit tracking for bulk products
    base_unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='pcs',
        help_text="Base unit of measurement"
    )
    unit_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Quantity in base units (e.g., 50 for 50kg, 0.5 for 500g)"
    )
    conversion_factor = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=1,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="How many of this unit equals 1 parent unit (e.g., 0.01 for 500g if parent is 50kg)"
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost price for profit calculation"
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Tax percentage (e.g., 16 for 16%)"
    )
    
    # Stock tracking
    stock_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(Decimal('0.000'))],
        help_text="For parent: number of bulk units (can be fractional). For child: calculated from parent"
    )
    min_stock_level = models.IntegerField(
        default=10,
        help_text="Minimum stock level for alerts"
    )
    
    # Other fields
    is_active = models.BooleanField(default=True)
    image = models.URLField(blank=True, null=True, help_text="Product image URL")
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    
    def __str__(self):
        if self.product_type == 'child' and self.parent_product:
            return f"{self.name} ({self.unit_quantity}{self.base_unit} from {self.parent_product.name})"
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        """Check if product is below minimum stock level"""
        if self.product_type == 'child' and self.parent_product:
            # For child products, check available stock from parent
            return self.available_child_stock <= self.min_stock_level
        return self.stock_quantity <= self.min_stock_level
    
    @property
    def available_child_stock(self):
        """
        For child products: calculate how many units are available from parent
        For parent/simple: return actual stock
        """
        if self.product_type == 'child' and self.parent_product:
            from decimal import Decimal
            parent_total_units = Decimal(str(self.parent_product.stock_quantity)) * self.parent_product.unit_quantity
            child_unit_size = Decimal(str(self.unit_quantity))
            if child_unit_size > 0:
                return int(parent_total_units / child_unit_size)
            return 0
        return self.stock_quantity
    
    @property
    def display_stock(self):
        """Display stock with units"""
        if self.product_type == 'parent':
            total_base_units = self.stock_quantity * self.unit_quantity
            return f"{self.stock_quantity} x {self.unit_quantity}{self.base_unit} = {total_base_units}{self.base_unit}"
        elif self.product_type == 'child':
            return f"{self.available_child_stock} units available"
        return f"{self.stock_quantity} units"
    
    @property
    def price_with_tax(self):
        """Calculate price including tax"""
        tax_amount = self.price * (Decimal(str(self.tax_rate)) / Decimal('100'))
        return self.price + tax_amount
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.price - self.cost_price) / self.cost_price) * Decimal('100')
        return 0
    
    def update_parent_stock(self, quantity_sold):
        """
        Reduce the parent's stock when this child product (a smaller portion) is sold.
        Example:
            Parent: 50 kg bag (stock_quantity = 10.0 bags)
            Child: 10 kg portion
            Sell 1 child (10kg) => parent stock goes from 10.0 → 9.8 bags
        """
        if self.product_type != 'child' or not self.parent_product:
            return Decimal('0')

        from decimal import Decimal

        parent = self.parent_product

        # Convert both quantities to the same base unit
        parent_unit_qty = Decimal(str(parent.unit_quantity))   # e.g., 50 kg
        child_unit_qty = Decimal(str(self.unit_quantity))       # e.g., 10 kg

        # How much of the parent is consumed
        total_child_qty_sold = Decimal(str(quantity_sold)) * child_unit_qty
        parent_units_consumed = total_child_qty_sold / parent_unit_qty

        previous_stock = Decimal(str(parent.stock_quantity))
        new_stock = previous_stock - parent_units_consumed

        if new_stock < 0:
            new_stock = Decimal('0')

        parent.stock_quantity = new_stock
        parent.save(update_fields=['stock_quantity'])

        return parent_units_consumed

        return 0
    
    def can_sell(self, quantity):
        """
        Check if we can sell the requested quantity
        For child products, checks parent stock availability
        """
        if self.product_type == 'child' and self.parent_product:
            return self.available_child_stock >= quantity
        return self.stock_quantity >= quantity
    
    def save(self, *args, **kwargs):
        # Validation: child products must have parent
        if self.product_type == 'child' and not self.parent_product:
            raise ValueError("Child products must have a parent product")
        
        # Validation: parent products cannot have parents
        if self.product_type == 'parent' and self.parent_product:
            raise ValueError("Parent products cannot have a parent")
        
        # Simple products shouldn't have parent
        if self.product_type == 'simple' and self.parent_product:
            self.parent_product = None
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['name']),
            models.Index(fields=['product_type']),
            models.Index(fields=['parent_product']),
        ]
    
class Medicine(models.Model):
    """
    Medicine catalog - can have multiple batches
    Replaces/extends Product for pharmacy use
    """
    MEDICINE_TYPE_CHOICES = [
        ('generic', 'Generic'),
        ('brand', 'Brand Name'),
    ]
    
    SCHEDULE_CHOICES = [
        ('otc', 'Over The Counter'),
        ('prescription', 'Prescription Only'),
        ('controlled', 'Controlled Drug')
    ]
    
    # Basic Info
    name = models.CharField(max_length=200, help_text="Brand or trade name")
    generic_name = models.CharField(max_length=200, help_text="Generic/scientific name")
    medicine_type = models.CharField(max_length=20, choices=MEDICINE_TYPE_CHOICES, default='generic')
    
    # Identification
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Classification
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name='medicines')
    schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='otc')
    
    # Details
    dosage_form = models.CharField(max_length=100, blank=True, help_text="e.g., Tablet, Syrup, Injection")
    strength = models.CharField(max_length=100, blank=True, help_text="e.g., 500mg, 10ml")
    manufacturer = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Pricing (default - can be overridden per batch)
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Storage & Safety
    storage_instructions = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    
    # Stock Tracking
    min_stock_level = models.IntegerField(default=10, help_text="Minimum total stock across all batches")
    reorder_level = models.IntegerField(default=20)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Audit
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_medicines')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.generic_name}) - {self.strength}"
    
    @property
    def total_stock(self):
        """Total stock across all non-expired batches"""
        return self.batches.filter(
            is_expired=False,
            quantity__gt=0
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def is_low_stock(self):
        """Check if total stock is below minimum level"""
        return self.total_stock <= self.min_stock_level
    
    @property
    def requires_prescription(self):
        """Check if medicine requires prescription"""
        return self.schedule in ['prescription', 'controlled']
    
    @property
    def is_controlled_drug(self):
        """Check if medicine is a controlled drug"""
        return self.schedule == 'controlled'
    
    class Meta:
        db_table = 'medicines'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['schedule']),
        ]
        
class Batch(models.Model):
    """
    Batch/Lot tracking for medicines
    Critical for FEFO and expiry management
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='batches')
    
    # Batch Identification
    batch_number = models.CharField(max_length=100)
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, related_name='batches')
    
    # Dates
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    
    # Quantity & Pricing
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current quantity in this batch"
    )
    initial_quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Original quantity received"
    )
    
    # Cost tracking
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Cost per unit"
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Selling price per unit"
    )
    
    # Status flags
    is_blocked = models.BooleanField(default=False, help_text="Manually blocked from sale")
    block_reason = models.TextField(blank=True)
    
    # Audit
    received_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='received_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medicine.name} - Batch {self.batch_number} (Exp: {self.expiry_date})"
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        return timezone.now().date() >= self.expiry_date
    
    @property
    def days_to_expiry(self):
        """Calculate days remaining until expiry"""
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    @property
    def is_near_expiry(self, days=90):
        """Check if batch is nearing expiry (default 90 days)"""
        return 0 < self.days_to_expiry <= days
    
    @property
    def can_dispense(self):
        """Check if batch can be dispensed"""
        return (
            not self.is_expired and 
            not self.is_blocked and 
            self.quantity > 0
        )
    
    @property
    def status(self):
        """Get batch status"""
        if self.is_expired:
            return 'expired'
        elif self.is_blocked:
            return 'blocked'
        elif self.is_near_expiry():
            return 'near_expiry'
        elif self.quantity == 0:
            return 'depleted'
        else:
            return 'available'
    
    def save(self, *args, **kwargs):
        # Auto-block expired batches
        if self.is_expired and not self.is_blocked:
            self.is_blocked = True
            self.block_reason = "Automatically blocked - expired"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'batches'
        ordering = ['expiry_date', 'batch_number']  # FEFO ordering
        unique_together = [['medicine', 'batch_number']]
        indexes = [
            models.Index(fields=['expiry_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['medicine', 'expiry_date']),
        ]
        
class StockReceiving(models.Model):
    """
    Record of stock received from supplier
    Links to batch creation
    """
    # Reference
    receiving_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey('Supplier', on_delete=models.PROTECT, related_name='stock_receivings')
    
    # Invoice details
    supplier_invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    # Totals
    total_items = models.IntegerField(default=0)
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )
    
    notes = models.TextField(blank=True)
    
    # Audit
    received_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='stock_receivings')
    received_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.receiving_number:
            from django.utils import timezone
            import uuid
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4())[:6].upper()
            self.receiving_number = f'RCV-{date_str}-{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.receiving_number} - {self.supplier.name}"
    
    class Meta:
        db_table = 'stock_receivings'
        ordering = ['-received_date']


class StockReceivingItem(models.Model):
    """
    Individual items in a stock receiving
    Creates/updates batches
    """
    receiving = models.ForeignKey(StockReceiving, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='receiving_items')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='receiving_items')
    
    # Batch details
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    manufacture_date = models.DateField(null=True, blank=True)
    
    # Quantity & Pricing
    quantity_received = models.IntegerField(validators=[MinValueValidator(1)])
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Calculated
    line_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.line_cost = self.purchase_price * self.quantity_received
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.quantity_received} units - Batch {self.batch_number}"
    
    class Meta:
        db_table = 'stock_receiving_items'


class MedicineStockMovement(models.Model):
    """
    Audit trail for all medicine stock movements
    Replaces/extends StockMovement for pharmacy
    """
    MOVEMENT_TYPE_CHOICES = [
        ('receiving', 'Stock Receiving'),
        ('sale', 'Sale/Dispensing'),
        ('adjustment', 'Manual Adjustment'),
        ('damage', 'Damage/Loss'),
        ('expiry_writeoff', 'Expired Stock Write-off'),
        ('return', 'Customer Return'),
        ('transfer', 'Transfer'),
    ]
    
    # What moved
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='medicine_movements')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='movements')
    
    # Movement details
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    
    # Stock levels
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    
    # References
    reference_number = models.CharField(max_length=100, blank=True)
    sale = models.ForeignKey('PharmacySale', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    receiving = models.ForeignKey(StockReceiving, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    
    # Reason for adjustment/damage
    reason = models.TextField(blank=True)
    
    # Audit
    performed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='medicine_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.movement_type} - {self.quantity}"
    
    class Meta:
        db_table = 'medicine_stock_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
            models.Index(fields=['batch', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]


class PharmacySale(models.Model):
    """
    Pharmacy-specific sale model
    Extended from Sale with prescription tracking
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'M-Pesa'),
        ('insurance', 'Insurance'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('voided', 'Voided'),
    ]
    
    # Basic sale info
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Prescription tracking
    has_prescription = models.BooleanField(default=False)
    prescription_number = models.CharField(max_length=100, blank=True)
    prescriber_name = models.CharField(max_length=200, blank=True)
    
    # Dispensing
    dispenser = models.ForeignKey('User', on_delete=models.PROTECT, related_name='dispensed_sales')
    
    # Financial
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    # Voiding
    voided_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='voided_sales')
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True)
    
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from django.utils import timezone
            import uuid
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4())[:8].upper()
            self.invoice_number = f'INV-{date_str}-{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_number} - KES {self.total}"
    
    class Meta:
        db_table = 'pharmacy_sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['dispenser', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]


class PharmacySaleItem(models.Model):
    """
    Individual items in a pharmacy sale
    Tracks batch dispensed from
    """
    sale = models.ForeignKey(PharmacySale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='sale_items')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='sale_items')
    
    # Item details (captured at time of sale)
    medicine_name = models.CharField(max_length=200)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    
    # Quantity & Pricing
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Calculated
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Prescription requirement
    requires_prescription = models.BooleanField(default=False)
    prescription_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        base_amount = self.unit_price * self.quantity
        discount = base_amount * (self.discount_percent / 100)
        self.subtotal = base_amount - discount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity} - Batch {self.batch_number}"
    
    class Meta:
        db_table = 'pharmacy_sale_items'


class ControlledDrugRegister(models.Model):
    """
    Special register for controlled drugs
    Legal requirement for tracking
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='controlled_drug_entries')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='controlled_drug_entries')
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('receiving', 'Stock Received'),
            ('dispensing', 'Dispensed'),
            ('adjustment', 'Adjustment'),
            ('writeoff', 'Write-off'),
        ]
    )
    
    quantity = models.IntegerField()
    balance = models.IntegerField(help_text="Running balance after transaction")
    
    # Patient/Customer details (for dispensing)
    customer_name = models.CharField(max_length=200, blank=True)
    prescription_number = models.CharField(max_length=100, blank=True)
    prescriber_name = models.CharField(max_length=200, blank=True)
    
    # Reference
    sale = models.ForeignKey(PharmacySale, on_delete=models.SET_NULL, null=True, blank=True, related_name='controlled_entries')
    receiving = models.ForeignKey(StockReceiving, on_delete=models.SET_NULL, null=True, blank=True, related_name='controlled_entries')
    
    # Authorization
    dispensed_by = models.ForeignKey('User', on_delete=models.PROTECT, related_name='controlled_dispensings')
    witnessed_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='witnessed_controlled')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.medicine.name} - {self.transaction_type} - {self.quantity} ({self.created_at.date()})"
    
    class Meta:
        db_table = 'controlled_drug_register'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
        ]
##
class Sale(models.Model):
    """Sales transaction"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'M-Pesa'),
    ]
    
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    cashier = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='sales'
    )
    customer_name = models.CharField(max_length=200, blank=True)
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    change_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate unique invoice number
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4())[:8].upper()
            self.invoice_number = f'INV-{date_str}-{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_number} - ${self.total}"
    
    class Meta:
        db_table = 'sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['cashier', '-created_at']),
            models.Index(fields=['-created_at']),
        ]


class SaleItem(models.Model):
    """Individual items in a sale"""
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    product_name = models.CharField(max_length=200)  # Store name at time of sale
    product_sku = models.CharField(max_length=50)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        base_amount = self.unit_price * self.quantity
        discount = base_amount * (self.discount_percent / 100)
        tax = (base_amount - discount) * (self.tax_rate / 100)
        self.subtotal = base_amount - discount + tax
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'sale_items'


class Payment(models.Model):
    """Payment details for a sale"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'M-Pesa'),
    ]
    
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_payment_method_display()} - ${self.amount}"
    
    class Meta:
        db_table = 'payments'
        
##
class Supplier(models.Model):
    """Suppliers for purchasing products"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['name']


class StockMovement(models.Model):
    """Track all stock movements (purchases, sales, adjustments)"""
    MOVEMENT_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damage/Loss'),
    ]
    
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT,
        related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField(help_text="Positive for stock in, negative for stock out")
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reference_number = models.CharField(max_length=100, blank=True, help_text="PO number, invoice, etc")
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    sale = models.ForeignKey(
        'Sale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements'
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]


class PurchaseOrder(models.Model):
    """Purchase orders for restocking"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate unique PO number
            import uuid
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = str(uuid.uuid4())[:6].upper()
            self.po_number = f'PO-{date_str}-{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-created_at']


class PurchaseOrderItem(models.Model):
    """Items in a purchase order"""
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    quantity_ordered = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_received = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.unit_cost * self.quantity_ordered
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity_ordered}"
    
    class Meta:
        db_table = 'purchase_order_items'


class StockAlert(models.Model):
    """Low stock alerts"""
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='stock_alerts'
    )
    alert_level = models.IntegerField()
    current_stock = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} - Low Stock Alert"
    
    class Meta:
        db_table = 'stock_alerts'
        ordering = ['-created_at']