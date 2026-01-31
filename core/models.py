from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Store(models.Model):
    """Pharmacy Store/Branch"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False, help_text='Mark this as the default store')
    is_active = models.BooleanField(default=True, help_text='Whether this store is active')
    address = models.TextField(blank=True)
    phone = models.CharField(blank=True, max_length=20)
    email = models.EmailField(blank=True)
    business_registration = models.CharField(max_length=100, blank=True, help_text='Business registration number')
    tax_id = models.CharField(max_length=100, blank=True, help_text='Tax ID/VAT number')
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_stores')
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


class Role(models.Model):
    """User roles for Pharmacy system"""
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
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    has_completed_setup = models.BooleanField(default=False, help_text='Whether the user has completed initial setup')
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


class Category(models.Model):
    """Medicine categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = [['name', 'store']]


class Medicine(models.Model):
    """Medicine catalog - can have multiple batches"""
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
    b_name = models.CharField(max_length=200, help_text="Brand or trade name")
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
    
    # Pricing
    buying_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
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
        return f"{self.b_name} ({self.generic_name}) - {self.strength}"
    
    @property
    def total_stock(self):
        """Total stock across all non-expired batches"""
        today = timezone.now().date()
        return self.batches.filter(
            expiry_date__gt=today,
            is_blocked=False
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
        ordering = ['b_name']
        indexes = [
            models.Index(fields=['b_name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['schedule']),
        ]


class Batch(models.Model):
    """Batch/Lot tracking for medicines - Critical for FEFO and expiry management"""
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='batches')
    
    # Batch Identification
    batch_number = models.CharField(max_length=100)
    supplier = models.ForeignKey('Supplier', on_delete=models.SET_NULL, null=True, blank=True, related_name='batches')
    
    # Dates
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField()
    received_date = models.DateField(auto_now_add=True)
    
    # Quantity & Pricing
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], help_text="Current quantity in this batch")
    initial_quantity = models.IntegerField(validators=[MinValueValidator(1)], help_text="Original quantity received")
    
    # Cost tracking
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))], help_text="Cost per unit")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Selling price per unit")
    
    # Status flags
    is_blocked = models.BooleanField(default=False, help_text="Manually blocked from sale")
    block_reason = models.TextField(blank=True)
    
    # Audit
    received_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='received_batches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medicine.b_name} - Batch {self.batch_number} (Exp: {self.expiry_date})"
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        from datetime import datetime
        if isinstance(self.expiry_date, str):
            expiry = datetime.strptime(self.expiry_date, '%Y-%m-%d').date()
        else:
            expiry = self.expiry_date
        return timezone.now().date() >= expiry
    
    @property
    def days_to_expiry(self):
        """Calculate days remaining until expiry"""
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    def is_near_expiry(self, days=90):
        """Check if batch is nearing expiry (default 90 days)"""
        return 0 < self.days_to_expiry <= days
    
    @property
    def can_dispense(self):
        """Check if batch can be dispensed"""
        return not self.is_expired and not self.is_blocked and self.quantity > 0
    
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
        if isinstance(self.expiry_date, str):
            from datetime import datetime
            self.expiry_date = datetime.strptime(self.expiry_date, '%Y-%m-%d').date()
        
        # Auto-block expired batches
        if self.is_expired and not self.is_blocked:
            self.is_blocked = True
            self.block_reason = "Automatically blocked - expired"
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'batches'
        ordering = ['expiry_date', 'batch_number']
        unique_together = [['medicine', 'batch_number']]
        indexes = [
            models.Index(fields=['expiry_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['medicine', 'expiry_date']),
        ]


class Supplier(models.Model):
    """Suppliers for medicine purchasing"""
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


class StockReceiving(models.Model):
    """Record of stock received from supplier"""
    receiving_number = models.CharField(max_length=50, unique=True, editable=False)
    supplier = models.ForeignKey('Supplier', on_delete=models.PROTECT, related_name='stock_receivings')
    
    # Invoice details
    supplier_invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    # Totals
    total_items = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])
    
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
    """Individual items in a stock receiving"""
    receiving = models.ForeignKey(StockReceiving, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name='receiving_items')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='receiving_items')
    
    # Batch details
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    manufacture_date = models.DateField(null=True, blank=True)
    
    # Quantity & Pricing
    quantity_received = models.IntegerField(validators=[MinValueValidator(1)])
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Calculated
    line_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        purchase_price = Decimal(str(self.purchase_price)) if self.purchase_price else Decimal('0')
        quantity = Decimal(str(self.quantity_received)) if self.quantity_received else Decimal('0')
        self.line_cost = purchase_price * quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine.b_name} - {self.quantity_received} units - Batch {self.batch_number}"
    
    class Meta:
        db_table = 'stock_receiving_items'


class MedicineStockMovement(models.Model):
    """Audit trail for all medicine stock movements"""
    MOVEMENT_TYPE_CHOICES = [
        ('receiving', 'Stock Receiving'),
        ('sale', 'Sale/Dispensing'),
        ('adjustment', 'Manual Adjustment'),
        ('damage', 'Damage/Loss'),
        ('expiry_writeoff', 'Expired Stock Write-off'),
        ('return', 'Customer Return'),
        ('transfer', 'Transfer'),
    ]
    
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
        return f"{self.medicine.b_name} - {self.movement_type} - {self.quantity}"
    
    class Meta:
        db_table = 'medicine_stock_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
            models.Index(fields=['batch', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
        ]


class PharmacySale(models.Model):
    """Pharmacy-specific sale model with prescription tracking"""
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
    """Individual items in a pharmacy sale"""
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
        base_amount = self.unit_price * self.quantity
        discount = base_amount * (self.discount_percent / 100)
        self.subtotal = base_amount - discount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.medicine_name} x {self.quantity} - Batch {self.batch_number}"
    
    class Meta:
        db_table = 'pharmacy_sale_items'


class ControlledDrugRegister(models.Model):
    """Special register for controlled drugs - Legal requirement for tracking"""
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
        return f"{self.medicine.b_name} - {self.transaction_type} - {self.quantity} ({self.created_at.date()})"
    
    class Meta:
        db_table = 'controlled_drug_register'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', '-created_at']),
        ]