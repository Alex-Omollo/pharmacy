import random
import uuid

def generate_barcode_number():
    """Generate a 13-digit EAN-style barcode number"""
    return str(random.randint(1000000000000, 9999999999999))

def generate_sku(name):
    """Generate a short human-readable SKU from product name"""
    prefix = name[:3].upper() if name else "SKU"
    suffix = uuid.uuid4().hex[:4].upper()
    return f"{prefix}-{suffix}"