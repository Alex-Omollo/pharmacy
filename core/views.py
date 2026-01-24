from rest_framework import status, generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg, F
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from .models import (
    User, Role, Product, Category,
    Sale, SaleItem, Payment, Supplier,
    StockMovement, PurchaseOrder, PurchaseOrderItem,
    StockAlert, Medicine, Batch, StockReceiving, MedicineStockMovement,
    PharmacySale, PharmacySaleItem, ControlledDrugRegister, Store
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, RoleSerializer, StoreSerializer, StoreCreateSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, CategorySerializer,
    BulkProductUploadSerializer, SaleListSerializer,
    SaleDetailSerializer, SaleCreateSerializer,
    SupplierSerializer, StockMovementSerializer, StockAdjustmentSerializer,
    PurchaseOrderCreateSerializer, PurchaseOrderDetailSerializer,
    PurchaseOrderListSerializer, StockAlertSerializer,
    ChildProductCreateSerializer, MedicineListSerializer, MedicineDetailSerializer,
    MedicineCreateUpdateSerializer, BatchListSerializer,
    BatchDetailSerializer, BatchCreateSerializer, BatchUpdateSerializer,
    StockReceivingListSerializer, StockReceivingDetailSerializer,
    StockReceivingCreateSerializer, PharmacySaleListSerializer,
    PharmacySaleDetailSerializer, PharmacySaleCreateSerializer,
    MedicineStockMovementSerializer, CompleteSetupSerializer
)
from .permissions import IsAdmin, IsManager, IsCashier
import io
import uuid
import csv
from datetime import datetime, timedelta
from decimal import Decimal
from .utils import generate_barcode_number, generate_sku
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import os

# ===== PATHS =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CERT_PATH = os.path.join(BASE_DIR, "certs", "certificate.pem")
PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "certs", "private-key.pem")


# ===== 1️⃣ GET CERTIFICATE (Public) =====
def get_qz_certificate(request):
    try:
        with open(CERT_PATH, "r") as file:
            cert_data = file.read()
        return HttpResponse(cert_data, content_type="text/plain")
    except FileNotFoundError:
        return JsonResponse({"error": "Certificate not found"}, status=404)


# ===== 2️⃣ SIGN DATA (Secure Signing) =====
def sign_qz_data(request):
    try:
        to_sign = request.GET.get("data")  # QZ sends plain string
        if not to_sign:
            return JsonResponse({"error": "Missing data to sign"}, status=400)

        # Load private key securely
        with open(PRIVATE_KEY_PATH, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None
            )

        # Sign using RSA SHA256
        signature = private_key.sign(
            to_sign.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        # Return Base64 signature
        return JsonResponse({
            "signature": base64.b64encode(signature).decode()
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include user data"""
    
    def validate(self, attrs):
        # Call parent validate to get default token data
        data = super().validate(attrs)
        
        # Get role-based token lifetime
        if self.user.role:
            role_name = self.user.role.name
            
            # Define role-based expiration times
            if role_name == 'cashier':
                access_lifetime = timedelta(hours=12)
                refresh_lifetime = timedelta(hours=12)
            elif role_name == 'admin':
                access_lifetime = timedelta(hours=4)
                refresh_lifetime = timedelta(hours=4)
            elif role_name == 'manager':
                access_lifetime = timedelta(hours=6)
                refresh_lifetime = timedelta(hours=6)
            else:
                access_lifetime = timedelta(minutes=30)
                refresh_lifetime = timedelta(hours=4)
                
            # Create new tokens with custom expiration
            refresh = RefreshToken.for_user(self.user)
            refresh.access_token.set_exp(lifetime=access_lifetime)
            refresh.set_exp(lifetime=refresh_lifetime)
            
            # Replace tokens in response
            data['access'] = str(refresh.access_token)
            data['refresh'] = str(refresh)
        
        # Add custom user data to the response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role.name if self.user.role else None,
            'role_display': self.user.role.get_name_display() if self.user.role else None,
        }
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with user data"""
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_setup_status(request):
    """Check if initial setup is required"""
    user = request.user
    
    setup_required = Store.setup_required()
    user_completed_setup = user.has_completed_setup
    
    return Response({
        'setup_required': setup_required,
        'user_completed_setup': user_completed_setup,
        'is_admin': user.is_admin,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.name if user.role else None,
        }
    })


@api_view(['POST'])
@permission_classes([IsAdmin])
def complete_initial_setup(request):
    """Complete initial store setup (Admin only)"""
    
    # Check if setup is already done
    if not Store.setup_required():
        return Response(
            {'error': 'Setup has already been completed'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = CompleteSetupSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        result = serializer.save()
        
        return Response({
            'message': 'Setup completed successfully!',
            'store': StoreSerializer(result['store']).data,
            'user': UserSerializer(result['user']).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ===== STORE MANAGEMENT VIEWS =====
class StoreListCreateView(generics.ListCreateAPIView):
    """List all stores or create new one (Admin only)"""
    # queryset = Store.objects.all()
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Store.objects.all()
        
        return Store.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoreCreateSerializer
        return StoreSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class StoreDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a store (Admin only)"""
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAdmin]
    
    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of default store"""
        store = self.get_object()
        
        if store.is_default:
            return Response(
                {'error': 'Cannot delete the default store'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if store.users.exists():
            return Response(
                {'error': f'Cannot delete store with {store.users.count()} associated users. Please reassign users first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_default_store(request):
    """Get the default store"""
    try:
        default_store = Store.get_default_store()
        serializer = StoreSerializer(default_store)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': 'Failed to get default store'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdmin])
def set_default_store(request, pk):
    """Set a store as the default store"""
    try:
        store = Store.objects.get(pk=pk)
        store.is_default = True
        store.save()
        
        return Response({
            'message': f'Store "{store.name}" set as default',
            'store': StoreSerializer(store).data
        })
    except Store.DoesNotExist:
        return Response(
            {'error': 'Store not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_store(request):
    """Get the current user's store"""
    user = request.user
    
    if user.store:
        serializer = StoreSerializer(user.store)
        return Response(serializer.data)
    else:
        # If user has no store, assign them to default store
        default_store = Store.get_default_store()
        if default_store:
            serializer = StoreSerializer(default_store)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No store assigned. Please complete setup.'},
                status=status.HTTP_404_NOT_FOUND
            )
        # user.store = default_store
        # user.save()
        
        # serializer = StoreSerializer(default_store)
        # return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    """User registration endpoint (Admin only)"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAdmin]


class UserListView(generics.ListAPIView):
    """List all users (Admin and Manager)"""
    queryset = User.objects.all().select_related('role')
    serializer_class = UserSerializer
    permission_classes = [IsManager]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail, update, delete (Admin only for modifications)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]
    
    def destroy(self, request, *args, **kwargs):
        """Delete user with validation"""
        user = self.get_object()
        # Prevent deleting yourself
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Prevent deleting the last admin
        if user.role and user.role.name == 'admin':
            admin_count = User.objects.filter(role__name='admin', is_active=True).count()
            if admin_count <= 1:
                return Response(
                    {'error': 'Cannot delete the last admin user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        user.delete()
        
        return Response(
            {'message': f'User {user.username} deleted successfully'},
            status=status.HTTP_200_OK
        )


class CurrentUserView(APIView):
    """Get current authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Wrong password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Update session
            update_session_auth_hash(request, user)
            
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleListView(generics.ListAPIView):
    """List all roles"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout_view(request):
    """Logout endpoint"""
    return Response(
        {'message': 'Logged out successfully.'},
        status=status.HTTP_200_OK
    )
    

##
class CategoryListCreateView(generics.ListCreateAPIView):
    """List all categories or create new one (Admin/Manager can create)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsManager()]
        return [IsCashier()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category (Admin/Manager only for modifications)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsManager()]
        return [IsCashier()]


class ProductListView(generics.ListAPIView):
    """List all products with search and filters"""
    serializer_class = ProductListSerializer
    permission_classes = [IsCashier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'barcode', 'category__name']
    ordering_fields = ['name', 'price', 'stock_quantity', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').all()
        
        # Filter out children from inventory(default)
        exclude_children = self.request.query_params.get('exclude_children', 'true')
        if exclude_children.lower() == 'true':
            queryset = queryset.exclude(product_type='child')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock', None)
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=models.F('min_stock_level'))
        
        return queryset

class ProductCreateView(generics.CreateAPIView):
    """Create new product (Admin/Manager only)"""
    queryset = Product.objects.all()
    serializer_class = ProductCreateUpdateSerializer
    permission_classes = [IsManager]
    
    def perform_create(self, serializer):
        name = serializer.validated_data.get('name', 'PRODUCT')
        
        # Generate SKU if not provided
        sku_value = serializer.validated_data.get('sku')
        if not sku_value:
            sku_value = generate_sku(name)
        
        # Generate barcode if not provided or is empty
        barcode_value = serializer.validated_data.get('barcode')
        if not barcode_value:
            barcode_value = generate_barcode_number()

        serializer.save(
            created_by=self.request.user,
            sku=sku_value,
            barcode=barcode_value
        )
        

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a product"""
    queryset = Product.objects.select_related('category', 'created_by').all()
    permission_classes = [IsCashier]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsManager()]
        return [IsCashier()]
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete: Mark product as inactive instead of deleting
        Only allow hard delete if product has no related records
        """
        product = self.get_object()
        
        # Check if product has related records
        has_sales = SaleItem.objects.filter(product=product).exists()
        has_stock_movements = StockMovement.objects.filter(product=product).exists()
        has_po_items = PurchaseOrderItem.objects.filter(product=product).exists()
        has_children = product.product_type == 'parent' and product.child_products.exists()
        
        if has_sales or has_stock_movements or has_po_items or has_children:
            # Soft delete - mark as inactive
            product.is_active = False
            product.save()
            
            return Response({
                'message': 'Product deactivated successfully',
                'note': 'Product cannot be permanently deleted because it has transaction history',
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'is_active': product.is_active
                }
            }, status=status.HTTP_200_OK)
        else:
            # Hard delete - no related records
            product_name = product.name
            product.delete()
            
            return Response({
                'message': f'Product "{product_name}" permanently deleted',
                'note': 'Product had no transaction history'
            }, status=status.HTTP_204_NO_CONTENT)
            
##
@api_view(['POST'])
@permission_classes([IsManager])
def deactivate_product(request, pk):
    """
    Deactivate a product (soft delete)
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not product.is_active:
        return Response(
            {'message': 'Product is already inactive'},
            status=status.HTTP_200_OK
        )
    
    product.is_active = False
    product.save()
    
    return Response({
        'message': f'Product "{product.name}" deactivated successfully',
        'product': ProductDetailSerializer(product).data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsManager])
def reactivate_product(request, pk):
    """
    Reactivate a deactivated product
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if product.is_active:
        return Response(
            {'message': 'Product is already active'},
            status=status.HTTP_200_OK
        )
    
    product.is_active = True
    product.save()
    
    return Response({
        'message': f'Product "{product.name}" reactivated successfully',
        'product': ProductDetailSerializer(product).data
    }, status=status.HTTP_200_OK)
    
@api_view(['DELETE'])
@permission_classes([IsAdmin])  # Only admins can force delete
def force_delete_product(request, pk):
    """
    Force delete a product and all related records
    WARNING: This is dangerous and should only be used by admins
    """
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check related records
    sales_count = SaleItem.objects.filter(product=product).count()
    movements_count = StockMovement.objects.filter(product=product).count()
    po_items_count = PurchaseOrderItem.objects.filter(product=product).count()
    children_count = product.child_products.count() if product.product_type == 'parent' else 0
    
    # Require confirmation
    confirm = request.data.get('confirm', False)
    
    if not confirm:
        return Response({
            'error': 'Confirmation required',
            'warning': 'This will permanently delete the product and affect transaction history',
            'impact': {
                'sales_affected': sales_count,
                'stock_movements_affected': movements_count,
                'purchase_orders_affected': po_items_count,
                'child_products_affected': children_count,
            },
            'note': 'Send "confirm": true to proceed with deletion'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Temporarily change PROTECT to CASCADE for deletion
    # This is done in a transaction to ensure atomicity
    product_name = product.name
    
    with transaction.atomic():
        # Delete related records manually
        SaleItem.objects.filter(product=product).delete()
        StockMovement.objects.filter(product=product).delete()
        PurchaseOrderItem.objects.filter(product=product).delete()
        
        # Child products will be deleted automatically due to CASCADE
        children_deleted = children_count
        
        # Finally delete the product
        product.delete()
    
    return Response({
        'message': f'Product "{product_name}" and all related records permanently deleted',
        'deleted': {
            'sales_items': sales_count,
            'stock_movements': movements_count,
            'purchase_order_items': po_items_count,
            'child_products': children_deleted
        }
    }, status=status.HTTP_200_OK)


class ProductSearchView(APIView):
    """Search products by name, SKU, or barcode"""
    permission_classes = [IsCashier]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'results': []})
        
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(barcode__icontains=query),
            is_active=True
        ).select_related('category')[:20]  # Limit to 20 results
        
        serializer = ProductListSerializer(products, many=True)
        return Response({'results': serializer.data})


class LowStockProductsView(generics.ListAPIView):
    """List products with low stock"""
    serializer_class = ProductListSerializer
    permission_classes = [IsManager]
    
    def get_queryset(self):
        from django.db.models import F
        return Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        ).exclude(
            product_type='child'
        ).select_related('category')


class BulkProductUploadView(APIView):
    """Bulk upload products via CSV (Admin/Manager only)"""
    permission_classes = [IsManager]
    
    def post(self, request):
        serializer = BulkProductUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = serializer.validated_data['csv_file']
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            created_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Get or create category
                    category = None
                    if row.get('category'):
                        category, _ = Category.objects.get_or_create(
                            name=row['category']
                        )
                    
                    # Create product
                    Product.objects.create(
                        name=row['name'],
                        sku=row['sku'],
                        barcode=row.get('barcode') or None,
                        category=category,
                        description=row.get('description', ''),
                        price=float(row['price']),
                        cost_price=float(row.get('cost_price', 0)),
                        tax_rate=float(row.get('tax_rate', 0)),
                        stock_quantity=int(row.get('stock_quantity', 0)),
                        min_stock_level=int(row.get('min_stock_level', 10)),
                        created_by=request.user
                    )
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            return Response({
                'message': f'Successfully created {created_count} products',
                'created_count': created_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error processing CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['GET'])
@permission_classes([IsManager])
def product_stats_view(request):
    """Get product statistics"""
    
    # EXCLUDE CHILD PRODUCTS from stats
    active_products = Product.objects.filter(is_active=True).exclude(product_type='child')
    
    stats = {
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_categories': Category.objects.filter(is_active=True).count(),
        'low_stock_products': Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        ).count(),
        'out_of_stock_products': Product.objects.filter(
            stock_quantity=0,
            is_active=True
        ).count(),
        'total_stock_value': Product.objects.filter(is_active=True).aggregate(
            total=Sum(F('stock_quantity') * F('cost_price'))
        )['total'] or 0,
    }
    
    return Response(stats)

##
class SaleListView(generics.ListAPIView):
    """List all sales with filters"""
    serializer_class = SaleListSerializer
    permission_classes = [IsCashier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'customer_name', 'cashier__username']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Sale.objects.select_related('cashier').all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            # Add one day to include the end date
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_datetime)
        
        # Filter by cashier
        cashier_id = self.request.query_params.get('cashier', None)
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)
        
        # Filter by payment method
        payment_method = self.request.query_params.get('payment_method', None)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Filter by status
        sale_status = self.request.query_params.get('status', None)
        if sale_status:
            queryset = queryset.filter(status=sale_status)
        
        # If cashier role, only show their own sales
        user = self.request.user
        if user.is_cashier and not (user.is_admin or user.is_manager):
            queryset = queryset.filter(cashier=user)
        
        return queryset


class SaleCreateView(generics.CreateAPIView):
    """Create a new sale"""
    serializer_class = SaleCreateSerializer
    permission_classes = [IsCashier]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        
        # Return detailed sale data
        detail_serializer = SaleDetailSerializer(sale)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class SaleDetailView(generics.RetrieveAPIView):
    """Get sale details"""
    queryset = Sale.objects.select_related('cashier').prefetch_related('items', 'payments').all()
    serializer_class = SaleDetailSerializer
    permission_classes = [IsCashier]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # If cashier, only show their own sales
        if user.is_cashier and not (user.is_admin or user.is_manager):
            queryset = queryset.filter(cashier=user)
        
        return queryset


@api_view(['GET'])
@permission_classes([IsCashier])
def sales_stats_view(request):
    """Get sales statistics"""
        
    # Date filters
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    
    queryset = Sale.objects.filter(status='completed')
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    # If cashier, only their sales
    user = request.user
    if user.is_cashier and not (user.is_admin or user.is_manager):
        queryset = queryset.filter(cashier=user)
    
    stats = queryset.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total'),
        average_sale=Avg('total'),
        total_items_sold=Sum('items__quantity')
    )
    
    # Payment method breakdown
    payment_breakdown = queryset.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total')
    )
    
    stats['payment_breakdown'] = list(payment_breakdown)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsManager])
def top_selling_products_view(request):
    """Get top selling products"""
    
    # Date filters
    days = int(request.query_params.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    top_products = SaleItem.objects.filter(
        sale__created_at__gte=start_date,
        sale__status='completed'
    ).values(
        'product__id',
        'product__name',
        'product__sku'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        times_sold=Count('id')
    ).order_by('-total_quantity')[:10]
    
    return Response(list(top_products))


@api_view(['POST'])
@permission_classes([IsManager])
def cancel_sale_view(request, pk):
    """Cancel a sale (Admin/Manager only)"""
    
    try:
        sale = Sale.objects.get(pk=pk)
    except Sale.DoesNotExist:
        return Response(
            {'error': 'Sale not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if sale.status == 'cancelled':
        return Response(
            {'error': 'Sale is already cancelled'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        # Restore stock
        for item in sale.items.all():
            product = item.product
            product.stock_quantity += item.quantity
            product.save()
        
        # Update sale status
        sale.status = 'cancelled'
        sale.save()
    
    return Response({
        'message': 'Sale cancelled successfully',
        'sale': SaleDetailSerializer(sale).data
    })
    
##
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter suppliers by user's store"""
        if self.request.user.is_superuser:
            return Supplier.objects.all()
        return Supplier.objects.filter(store=self.request.user.store)
        
        
    def perform_create(self, serializer):
        user = self.request.user
        store = user.store if user.store else Store.get_default_store()
        
        if not store:
            raise ValidationError('No store available. Please contact administrator')
        
        serializer.save(store=store)
        
        # if not hasattr(user, "store") or user.store is None:
        #     raise ValidationError("User is not assigned to a store")
        # serializer.save(store=user.store)



class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsManager]


# Stock Movement Views
class StockMovementListView(generics.ListAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [IsManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product__name', 'product__sku', 'reference_number']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = StockMovement.objects.select_related(
            'product', 'supplier', 'user'
        ).all()
        
        # Filter by product
        product_id = self.request.query_params.get('product', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by movement type
        movement_type = self.request.query_params.get('movement_type', None)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        return queryset


class StockAdjustmentView(APIView):
    """Manual stock adjustment"""
    permission_classes = [IsManager]
    
    def post(self, request):
        serializer = StockAdjustmentSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        product = validated_data['_product']
        adjustment_type = validated_data['adjustment_type']
        quantity = validated_data['quantity']
        
        with transaction.atomic():
            previous_quantity = product.stock_quantity
            
            # Calculate new quantity
            if adjustment_type == 'add':
                new_quantity = previous_quantity + quantity
                movement_quantity = quantity
            elif adjustment_type == 'remove':
                new_quantity = previous_quantity - quantity
                movement_quantity = -quantity
            else:  # set
                new_quantity = quantity
                movement_quantity = quantity - previous_quantity
            
            # Update product stock
            product.stock_quantity = new_quantity
            product.save()
            
            # Create stock movement record
            movement = StockMovement.objects.create(
                product=product,
                movement_type='adjustment',
                quantity=movement_quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                reference_number=validated_data.get('reference_number', ''),
                user=request.user,
                notes=validated_data['reason']
            )
            
            # Check for low stock alert
            if new_quantity <= product.min_stock_level:
                StockAlert.objects.get_or_create(
                    product=product,
                    is_resolved=False,
                    defaults={
                        'alert_level': product.min_stock_level,
                        'current_stock': new_quantity
                    }
                )
        
        return Response({
            'message': 'Stock adjusted successfully',
            'movement': StockMovementSerializer(movement).data
        }, status=status.HTTP_200_OK)


# Purchase Order Views
class PurchaseOrderListView(generics.ListAPIView):
    serializer_class = PurchaseOrderListSerializer
    permission_classes = [IsManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['po_number', 'supplier__name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
        
        # Filter by status
        po_status = self.request.query_params.get('status', None)
        if po_status:
            queryset = queryset.filter(status=po_status)
        
        return queryset


class PurchaseOrderCreateView(generics.CreateAPIView):
    serializer_class = PurchaseOrderCreateSerializer
    permission_classes = [IsManager]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        po = serializer.save()
        
        detail_serializer = PurchaseOrderDetailSerializer(po)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class PurchaseOrderDetailView(generics.RetrieveAPIView):
    queryset = PurchaseOrder.objects.prefetch_related('items__product').all()
    serializer_class = PurchaseOrderDetailSerializer
    permission_classes = [IsManager]


@api_view(['POST'])
@permission_classes([IsManager])
def receive_purchase_order(request, pk):
    """Mark purchase order as received and update stock"""
    try:
        po = PurchaseOrder.objects.get(pk=pk)
    except PurchaseOrder.DoesNotExist:
        return Response(
            {'error': 'Purchase order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if po.status == 'received':
        return Response(
            {'error': 'Purchase order already received'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    with transaction.atomic():
        # Update stock for each item
        for item in po.items.all():
            product = item.product
            previous_quantity = product.stock_quantity
            new_quantity = previous_quantity + item.quantity_ordered
            
            # Update product stock
            product.stock_quantity = new_quantity
            product.save()
            
            # Update item received quantity
            item.quantity_received = item.quantity_ordered
            item.save()
            
            # Create stock movement
            StockMovement.objects.create(
                product=product,
                movement_type='purchase',
                quantity=item.quantity_ordered,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                unit_cost=item.unit_cost,
                reference_number=po.po_number,
                supplier=po.supplier,
                user=request.user,
                notes=f'Received from PO {po.po_number}'
            )
            
            # Resolve low stock alerts if any
            StockAlert.objects.filter(
                product=product,
                is_resolved=False
            ).update(
                is_resolved=True,
                resolved_at=timezone.now()
            )
        
        # Update PO status
        po.status = 'received'
        po.received_date = timezone.now()
        po.save()
    
    return Response({
        'message': 'Purchase order received successfully',
        'po': PurchaseOrderDetailSerializer(po).data
    })


@api_view(['POST'])
@permission_classes([IsManager])
def cancel_purchase_order(request, pk):
    """Cancel a purchase order"""
    try:
        po = PurchaseOrder.objects.get(pk=pk)
    except PurchaseOrder.DoesNotExist:
        return Response(
            {'error': 'Purchase order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if po.status == 'received':
        return Response(
            {'error': 'Cannot cancel a received purchase order'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    po.status = 'cancelled'
    po.save()
    
    return Response({
        'message': 'Purchase order cancelled successfully',
        'po': PurchaseOrderDetailSerializer(po).data
    })


# Stock Alert Views
class StockAlertListView(generics.ListAPIView):
    serializer_class = StockAlertSerializer
    permission_classes = [IsManager]
    
    def get_queryset(self):
        # Only show unresolved alerts
        return StockAlert.objects.filter(
            is_resolved=False
        ).exclude(
            product__product_type='child'    
        ).select_related('product')


@api_view(['GET'])
@permission_classes([IsManager])
def inventory_stats_view(request):
    """Get inventory statistics"""
    
    # Exclude child products
    base_products = Product.objects.filter(is_active=True).exclude(product_type='child')
    
    stats = {
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_stock_value': Product.objects.filter(is_active=True).aggregate(
            total=Sum(F('stock_quantity') * F('cost_price'))
        )['total'] or 0,
        'low_stock_count': Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            is_active=True
        ).count(),
        'out_of_stock_count': Product.objects.filter(
            stock_quantity=0,
            is_active=True
        ).count(),
        'active_alerts': StockAlert.objects.filter(
            is_resolved=False,
            product__is_active=True   
        ).exclude(product__product_type='child').count(),
        'pending_pos': PurchaseOrder.objects.filter(status='pending').count(),
    }
    
    return Response(stats)

## 
@api_view(['GET'])
@permission_classes([IsManager])
def sales_report_view(request):
    """Comprehensive sales report with filters"""
    # Get date range from query params
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    period = request.query_params.get('period', 'daily')  # daily, weekly, monthly
    cashier_id = request.query_params.get('cashier')
    
    # Base queryset
    queryset = Sale.objects.filter(status='completed')
    
    # Apply filters
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    else:
        # Default to last 30 days
        start_date = (datetime.now() - timedelta(days=30)).date()
        queryset = queryset.filter(created_at__gte=start_date)
    
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    if cashier_id:
        queryset = queryset.filter(cashier_id=cashier_id)
    
    # Aggregate data based on period
    if period == 'daily':
        sales_by_period = queryset.annotate(
            period=TruncDate('created_at')
        ).values('period').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            average_sale=Avg('total')
        ).order_by('period')
    elif period == 'weekly':
        sales_by_period = queryset.annotate(
            period=TruncWeek('created_at')
        ).values('period').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            average_sale=Avg('total')
        ).order_by('period')
    else:  # monthly
        sales_by_period = queryset.annotate(
            period=TruncMonth('created_at')
        ).values('period').annotate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            average_sale=Avg('total')
        ).order_by('period')
    
    # Overall statistics
    overall_stats = queryset.aggregate(
        total_sales=Count('id'),
        total_revenue=Sum('total'),
        average_sale=Avg('total'),
        total_discount=Sum('discount_amount'),
        total_tax=Sum('tax_amount')
    )
    
    # Payment method breakdown
    payment_breakdown = queryset.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('total')
    )
    
    # Top cashiers
    top_cashiers = queryset.values(
        'cashier__id',
        'cashier__username',
        'cashier__first_name',
        'cashier__last_name'
    ).annotate(
        total_sales=Count('id'),
        total_revenue=Sum('total')
    ).order_by('-total_revenue')[:10]
    
    return Response({
        'period': period,
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'overall_stats': overall_stats,
        'sales_by_period': list(sales_by_period),
        'payment_breakdown': list(payment_breakdown),
        'top_cashiers': list(top_cashiers)
    })


@api_view(['GET'])
@permission_classes([IsManager])
def product_performance_report_view(request):
    """Product performance and profitability report"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    limit = int(request.query_params.get('limit', 20))
    
    # Base queryset
    queryset = SaleItem.objects.filter(sale__status='completed')
    
    # Apply date filters
    if start_date:
        queryset = queryset.filter(sale__created_at__gte=start_date)
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(sale__created_at__lt=end_datetime)
    
    # Top selling products by quantity
    top_products_qty = queryset.values(
        'product__id',
        'product__name',
        'product__sku',
        'product__cost_price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal'),
        times_sold=Count('sale')
    ).order_by('-total_quantity')[:limit]
    
    # Calculate profit for each product
    top_products_list = list(top_products_qty)
    for product in top_products_list:
        cost_price = product['product__cost_price']
        revenue = product['total_revenue']
        quantity = product['total_quantity']
        
        if cost_price and quantity:
            total_cost = cost_price * quantity
            profit = revenue - total_cost
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            product['total_cost'] = float(total_cost)
            product['profit'] = float(profit)
            product['profit_margin'] = round(float(profit_margin), 2)
        else:
            product['total_cost'] = 0
            product['profit'] = 0
            product['profit_margin'] = 0
    
    # Top products by revenue
    top_products_revenue = queryset.values(
        'product__id',
        'product__name',
        'product__sku'
    ).annotate(
        total_revenue=Sum('subtotal'),
        total_quantity=Sum('quantity')
    ).order_by('-total_revenue')[:limit]
    
    # Low performing products
    low_performing = queryset.values(
        'product__id',
        'product__name',
        'product__sku'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('total_quantity')[:10]
    
    return Response({
        'top_products_by_quantity': top_products_list,
        'top_products_by_revenue': list(top_products_revenue),
        'low_performing_products': list(low_performing)
    })


@api_view(['GET'])
@permission_classes([IsManager])
def cashier_performance_report_view(request):
    """Cashier performance report"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Base queryset
    queryset = Sale.objects.filter(status='completed')
    
    # Apply date filters
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    # Cashier performance
    cashier_stats = queryset.values(
        'cashier__id',
        'cashier__username',
        'cashier__first_name',
        'cashier__last_name'
    ).annotate(
        total_sales=Count('id'),
        total_revenue=Sum('total'),
        average_sale=Avg('total'),
        total_items_sold=Sum('items__quantity'),
        total_discount_given=Sum('discount_amount')
    ).order_by('-total_revenue')
    
    # Sales by payment method per cashier
    cashier_payment_methods = queryset.values(
        'cashier__username',
        'payment_method'
    ).annotate(
        count=Count('id'),
        total=Sum('total')
    )
    
    return Response({
        'cashier_performance': list(cashier_stats),
        'payment_methods_by_cashier': list(cashier_payment_methods)
    })


@api_view(['GET'])
@permission_classes([IsManager])
def inventory_report_view(request):
    """Inventory valuation and status report"""
    
    # Stock valuation
    products = Product.objects.filter(
        is_active=True
    ).exclude(
        product_type='child'
    ).annotate(
        stock_value=F('stock_quantity') * F('cost_price')
    )
    
    total_stock_value = products.aggregate(
        total=Sum('stock_value')
    )['total'] or 0
    
    # Stock status breakdown
    in_stock = products.filter(stock_quantity__gt=F('min_stock_level')).count()
    low_stock = products.filter(
        stock_quantity__lte=F('min_stock_level'),
        stock_quantity__gt=0
    ).count()
    out_of_stock = products.filter(stock_quantity=0).count()
    
    # Top value inventory items
    top_value_items = products.order_by('-stock_value')[:10].values(
        'id', 'name', 'sku', 'stock_quantity', 'cost_price', 'stock_value'
    )
    
    # Fast moving products (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    fast_moving = SaleItem.objects.filter(
        sale__created_at__gte=thirty_days_ago,
        sale__status='completed'
    ).values(
        'product__id',
        'product__name',
        'product__sku'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:10]
    
    # Slow moving products
    slow_moving = SaleItem.objects.filter(
        sale__created_at__gte=thirty_days_ago,
        sale__status='completed'
    ).values(
        'product__id',
        'product__name',
        'product__sku'
    ).annotate(
        total_sold=Sum('quantity')
    ).order_by('total_sold')[:10]
    
    return Response({
        'total_stock_value': float(total_stock_value),
        'stock_status': {
            'in_stock': in_stock,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock
        },
        'top_value_items': list(top_value_items),
        'fast_moving_products': list(fast_moving),
        'slow_moving_products': list(slow_moving)
    })


@api_view(['GET'])
@permission_classes([IsManager])
def dashboard_stats_view(request):
    """Dashboard overview statistics"""
    # Get date range (default last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    seven_days_ago = datetime.now() - timedelta(days=7)
    today = datetime.now().date()
    
    # Sales statistics
    total_sales = Sale.objects.filter(status='completed').count()
    sales_today = Sale.objects.filter(
        status='completed',
        created_at__date=today
    ).aggregate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    sales_this_week = Sale.objects.filter(
        status='completed',
        created_at__gte=seven_days_ago
    ).aggregate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    sales_this_month = Sale.objects.filter(
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    # Product statistics
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        is_active=True
    ).count()
    
    # Recent sales trend (last 7 days)
    sales_trend = Sale.objects.filter(
        status='completed',
        created_at__gte=seven_days_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('date')
    
    return Response({
        'total_sales': total_sales,
        'today': {
            'sales': sales_today['count'] or 0,
            'revenue': float(sales_today['revenue'] or 0)
        },
        'this_week': {
            'sales': sales_this_week['count'] or 0,
            'revenue': float(sales_this_week['revenue'] or 0)
        },
        'this_month': {
            'sales': sales_this_month['count'] or 0,
            'revenue': float(sales_this_month['revenue'] or 0)
        },
        'total_products': total_products,
        'low_stock_alerts': low_stock_count,
        'sales_trend': list(sales_trend)
    })


@api_view(['GET'])
@permission_classes([IsManager])
def export_sales_report_csv(request):
    """Export sales report as CSV"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    queryset = Sale.objects.filter(status='completed').select_related('cashier')
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Invoice Number', 'Date', 'Cashier', 'Customer',
        'Subtotal', 'Tax', 'Discount', 'Total', 'Payment Method'
    ])
    
    for sale in queryset:
        writer.writerow([
            sale.invoice_number,
            sale.created_at.strftime('%Y-%m-%d %H:%M'),
            sale.cashier.username,
            sale.customer_name or 'Walk-in',
            sale.subtotal,
            sale.tax_amount,
            sale.discount_amount,
            sale.total,
            sale.get_payment_method_display()
        ])
    
    return response

@api_view(['POST'])
@permission_classes([IsManager])
def create_bulk_parent_product(request):
    """
    Create a parent/bulk product
    Example: 50kg Rice Bag
    """
    serializer = ProductCreateUpdateSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate SKU if not provided
    validated_data = serializer.validated_data
    if not validated_data.get('sku'):
        name = validated_data.get('name', 'PRODUCT')
        validated_data['sku'] = generate_sku(name)
    
    # Generate barcode if not provided or empty
    if not validated_data.get('barcode'):
        validated_data['barcode'] = generate_barcode_number()
    
    # Set product type to parent
    product = serializer.save(
        created_by=request.user,
        product_type='parent'
    )
    
    return Response({
        'message': 'Parent product created successfully',
        'product': ProductDetailSerializer(product).data
    }, status=status.HTTP_201_CREATED)
    

@api_view(['POST'])
@permission_classes([IsManager])
def create_child_products_from_parent(request):
    """
    Create multiple child products from a parent product
    Names are auto-generated from parent name + unit quantity
    
    Example request:
    {
        "parent_id": 1,
        "child_products": [
            {
                "unit_quantity": 0.5,
                "price": 50.00,
                "cost_price": 30.00
            },
            {
                "unit_quantity": 1,
                "price": 95.00,
                "cost_price": 55.00
            }
        ]
    }
    """
    parent_id = request.data.get('parent_id')
    child_products_data = request.data.get('child_products', [])
    
    if not parent_id:
        return Response(
            {'error': 'parent_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not child_products_data:
        return Response(
            {'error': 'At least one child product is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        parent_product = Product.objects.get(id=parent_id, product_type='parent')
    except Product.DoesNotExist:
        return Response(
            {'error': 'Parent product not found or is not a parent type'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    created_children = []
    errors = []
    
    with transaction.atomic():
        for child_data in child_products_data:
            try:
                # Get unit_quantity and price (required fields)
                unit_quantity = child_data.get('unit_quantity')
                price = child_data.get('price')
                
                # Validate required fields are present
                if not unit_quantity:
                    errors.append({
                        'product': 'Unknown',
                        'error': 'Unit quantity is required'
                    })
                    continue
                    
                if not price:
                    errors.append({
                        'product': 'Unknown',
                        'error': 'Price is required'
                    })
                    continue
                
                # Convert to Decimal for calculations
                try:
                    unit_qty_decimal = Decimal(str(unit_quantity))
                    price_decimal = Decimal(str(price))
                except (ValueError, TypeError):
                    errors.append({
                        'product': 'Unknown',
                        'error': 'Invalid number format for unit_quantity or price'
                    })
                    continue
                
                # Validate positive values
                if unit_qty_decimal <= 0:
                    errors.append({
                        'product': 'Unknown',
                        'error': 'Unit quantity must be greater than 0'
                    })
                    continue
                    
                if price_decimal <= 0:
                    errors.append({
                        'product': 'Unknown',
                        'error': 'Price must be greater than 0'
                    })
                    continue
                
                # AUTO-GENERATE NAME from parent name + unit quantity
                # Format: "Parent Name 500g", "Parent Name 1kg", etc.
                if unit_qty_decimal < 1 and parent_product.base_unit in ['kg', 'l']:
                    # Convert to smaller unit (g or ml)
                    small_qty = unit_qty_decimal * 1000
                    small_unit = 'g' if parent_product.base_unit == 'kg' else 'ml'
                    name = f"{parent_product.name} {int(small_qty)}{small_unit}"
                else:
                    # Use the parent's base unit
                    # Format decimal nicely (remove trailing zeros)
                    if unit_qty_decimal == unit_qty_decimal.to_integral_value():
                        qty_str = str(int(unit_qty_decimal))
                    else:
                        qty_str = str(unit_qty_decimal)
                    name = f"{parent_product.name} {qty_str}{parent_product.base_unit}"
                
                # Allow custom name override if provided
                custom_name = child_data.get('name', '').strip()
                if custom_name:
                    name = custom_name
                
                # Get cost_price (optional, defaults to 0)
                cost_price = Decimal(str(child_data.get('cost_price', 0))) if child_data.get('cost_price') else Decimal('0')
                
                # Calculate conversion factor
                parent_unit = Decimal(str(parent_product.unit_quantity))
                conversion_factor = unit_qty_decimal / parent_unit
                
                # Generate SKU if not provided
                sku = child_data.get('sku', '').strip()
                if not sku:
                    sku = generate_sku(name)
                
                # Generate barcode if not provided or empty
                barcode = child_data.get('barcode', '').strip()
                if not barcode:
                    barcode = generate_barcode_number()
                
                # Create child product
                child = Product.objects.create(
                    name=name,
                    sku=sku,
                    barcode=barcode,
                    category=parent_product.category,
                    description=child_data.get('description', f"Derived from {parent_product.name}"),
                    product_type='child',
                    parent_product=parent_product,
                    base_unit=parent_product.base_unit,
                    unit_quantity=unit_qty_decimal,
                    conversion_factor=conversion_factor,
                    price=price_decimal,
                    cost_price=cost_price,
                    tax_rate=Decimal(str(child_data.get('tax_rate', parent_product.tax_rate))),
                    stock_quantity=0,  # Child stock is calculated from parent
                    min_stock_level=int(child_data.get('min_stock_level', 10)),
                    is_active=True,
                    created_by=request.user
                )
                created_children.append(child)
                
            except Exception as e:
                errors.append({
                    'product': 'Unknown',
                    'error': str(e)
                })
    
    if created_children:
        return Response({
            'message': f'Created {len(created_children)} child products',
            'created': [{
                'id': child.id,
                'name': child.name,
                'sku': child.sku,
                'unit_quantity': str(child.unit_quantity),
                'available_stock': child.available_child_stock
            } for child in created_children],
            'errors': errors
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'message': 'No child products were created',
            'errors': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
@permission_classes([IsManager])
def parent_product_children(request, parent_id):
    """Get all child products of a parent product"""
    try:
        parent = Product.objects.get(id=parent_id, product_type='parent')
    except Product.DoesNotExist:
        return Response(
            {'error': 'Parent product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    children = parent.child_products.filter(is_active=True)
    
    return Response({
        'parent': {
            'id': parent.id,
            'name': parent.name,
            'stock_quantity': parent.stock_quantity,
            'unit_quantity': str(parent.unit_quantity),
            'base_unit': parent.base_unit,
            'total_base_units': float(parent.stock_quantity) * float(parent.unit_quantity)
        },
        'children': [{
            'id': child.id,
            'name': child.name,
            'sku': child.sku,
            'unit_quantity': str(child.unit_quantity),
            'base_unit': child.base_unit,
            'price': str(child.price),
            'available_stock': child.available_child_stock,
            'is_low_stock': child.is_low_stock
        } for child in children]
    })


@api_view(['POST'])
@permission_classes([IsManager])
def update_parent_stock(request, parent_id):
    """
    Update parent product stock
    This will automatically update available stock for all child products
    """
    try:
        parent = Product.objects.get(id=parent_id, product_type='parent')
    except Product.DoesNotExist:
        return Response(
            {'error': 'Parent product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    new_stock = request.data.get('stock_quantity')
    if new_stock is None:
        return Response(
            {'error': 'stock_quantity is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        new_stock = int(new_stock)
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_stock = parent.stock_quantity
    parent.stock_quantity = new_stock
    parent.save()
    
    # Get updated child stock availability
    children_update = [{
        'id': child.id,
        'name': child.name,
        'available_stock': child.available_child_stock
    } for child in parent.child_products.filter(is_active=True)]
    
    return Response({
        'message': 'Parent stock updated successfully',
        'parent': {
            'id': parent.id,
            'name': parent.name,
            'old_stock': old_stock,
            'new_stock': new_stock,
            'total_base_units': float(new_stock) * float(parent.unit_quantity)
        },
        'children_availability': children_update
    })


@api_view(['GET'])
def product_stock_info(request, product_id):
    """Get detailed stock information for any product type"""
    try:
        product = Product.objects.select_related('parent_product', 'category').get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    response_data = {
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'product_type': product.product_type,
        'base_unit': product.base_unit,
        'unit_quantity': str(product.unit_quantity),
        'display_stock': product.display_stock,
        'is_low_stock': product.is_low_stock,
        'is_active': product.is_active,
        'price': str(product.price)
    }
    
    if product.product_type == 'parent':
        response_data['stock_quantity'] = product.stock_quantity
        response_data['total_base_units'] = float(product.stock_quantity) * float(product.unit_quantity)
        response_data['child_count'] = product.child_products.filter(is_active=True).count()
        
        # Include children info
        children = product.child_products.filter(is_active=True)
        response_data['children'] = [{
            'id': child.id,
            'name': child.name,
            'sku': child.sku,
            'unit_quantity': str(child.unit_quantity),
            'available_stock': child.available_child_stock,
            'price': str(child.price),
            'is_low_stock': child.is_low_stock
        } for child in children]
        
    elif product.product_type == 'child':
        response_data['parent'] = {
            'id': product.parent_product.id,
            'name': product.parent_product.name,
            'stock_quantity': product.parent_product.stock_quantity,
            'unit_quantity': str(product.parent_product.unit_quantity),
            'total_base_units': float(product.parent_product.stock_quantity) * float(product.parent_product.unit_quantity)
        }
        response_data['available_stock'] = product.available_child_stock
        response_data['conversion_factor'] = str(product.conversion_factor)
        response_data['calculation'] = f"{response_data['parent']['total_base_units']}{product.base_unit} ÷ {product.unit_quantity}{product.base_unit} = {product.available_child_stock} units"
        
    else:  # simple
        response_data['stock_quantity'] = product.stock_quantity
        response_data['available_stock'] = product.stock_quantity
    
    return Response(response_data)

@api_view(['POST'])
@permission_classes([IsAdmin])
def reset_user_password(request, pk):
    """
    Admin can reset any user's password
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    new_password = request.data.get('new_password')
    
    if not new_password:
        return Response(
            {'error': 'New password is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'message': f'Password for {user.username} has been reset successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_own_password(request):
    """
    User can change their own password
    Requires old password for verification
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not old_password or not new_password:
        return Response(
            {'error': 'Both old and new passwords are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify old password
    if not user.check_password(old_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Update session to prevent logout
    update_session_auth_hash(request, user)
    
    return Response({
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)
    
# ============================
# Medicine views
# ============================

class MedicineListView(generics.ListAPIView):
    """List all medicines with search and filters"""
    serializer_class = MedicineListSerializer
    permission_classes = [IsCashier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['b_name', 'generic_name', 'sku', 'barcode', 'manufacturer']
    ordering_fields = ['b_name', 'generic_name', 'price', 'cost_price', 'created_at']
    ordering = ['b_name']
    
    def get_queryset(self):
        queryset = Medicine.objects.select_related('category').all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', 'true')
        if is_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by schedule (prescription requirement)
        schedule = self.request.query_params.get('schedule')
        if schedule:
            queryset = queryset.filter(schedule=schedule)
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            # This will need annotation
            pass
        
        return queryset


class MedicineCreateView(generics.CreateAPIView):
    """Create new medicine"""
    queryset = Medicine.objects.all()
    serializer_class = MedicineCreateUpdateSerializer
    permission_classes = [IsManager]
    
    def perform_create(self, serializer):
        from .utils import generate_sku, generate_barcode_number
        
        name = serializer.validated_data.get('b_name', 'MEDICINE')
        sku = serializer.validated_data.get('sku')
        if not sku:
            sku = generate_sku(name)
        
        barcode = serializer.validated_data.get('barcode')
        if not barcode:
            barcode = generate_barcode_number()
        
        serializer.save(
            created_by=self.request.user,
            sku=sku,
            barcode=barcode
        )


class MedicineDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update medicine"""
    queryset = Medicine.objects.select_related('category').all()
    permission_classes = [IsCashier]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MedicineCreateUpdateSerializer
        return MedicineDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsManager()]
        return [IsCashier()]


@api_view(['POST'])
@permission_classes([IsManager])
def deactivate_medicine(request, pk):
    """Deactivate a medicine (soft delete)"""
    try:
        medicine = Medicine.objects.get(pk=pk)
    except Medicine.DoesNotExist:
        return Response({'error': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)
    
    medicine.is_active = False
    medicine.save()
    
    return Response({
        'message': f'Medicine "{medicine.name}" deactivated successfully',
        'medicine': MedicineDetailSerializer(medicine).data
    })


@api_view(['POST'])
@permission_classes([IsManager])
def reactivate_medicine(request, pk):
    """Reactivate a medicine"""
    try:
        medicine = Medicine.objects.get(pk=pk)
    except Medicine.DoesNotExist:
        return Response({'error': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)
    
    medicine.is_active = True
    medicine.save()
    
    return Response({
        'message': f'Medicine "{medicine.name}" reactivated successfully',
        'medicine': MedicineDetailSerializer(medicine).data
    })


# ============================================================================
# BATCH VIEWS
# ============================================================================

class BatchListView(generics.ListAPIView):
    """List all batches with filters"""
    serializer_class = BatchListSerializer
    permission_classes = [IsCashier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['batch_number', 'medicine__name', 'medicine__generic_name']
    ordering_fields = ['expiry_date', 'received_date', 'quantity']
    ordering = ['expiry_date']
    
    def get_queryset(self):
        queryset = Batch.objects.select_related('medicine', 'supplier').all()
        
        # Filter by medicine
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'available':
            queryset = queryset.filter(
                is_expired=False,
                is_blocked=False,
                quantity__gt=0
            )
        elif status_filter == 'expired':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date())
        elif status_filter == 'near_expiry':
            near_date = timezone.now().date() + timedelta(days=90)
            queryset = queryset.filter(
                expiry_date__lte=near_date,
                expiry_date__gt=timezone.now().date()
            )
        elif status_filter == 'blocked':
            queryset = queryset.filter(is_blocked=True)
        
        return queryset


class BatchDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update batch"""
    queryset = Batch.objects.select_related('medicine', 'supplier').all()
    permission_classes = [IsCashier]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BatchUpdateSerializer
        return BatchDetailSerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsManager()]
        return [IsCashier()]


@api_view(['POST'])
@permission_classes([IsManager])
def block_batch(request, pk):
    """Block a batch from sale"""
    try:
        batch = Batch.objects.get(pk=pk)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
    
    reason = request.data.get('reason', 'Manually blocked')
    
    batch.is_blocked = True
    batch.block_reason = reason
    batch.save()
    
    return Response({
        'message': f'Batch {batch.batch_number} blocked successfully',
        'batch': BatchDetailSerializer(batch).data
    })


@api_view(['POST'])
@permission_classes([IsManager])
def unblock_batch(request, pk):
    """Unblock a batch"""
    try:
        batch = Batch.objects.get(pk=pk)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if batch.is_expired:
        return Response(
            {'error': 'Cannot unblock expired batch'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    batch.is_blocked = False
    batch.block_reason = ''
    batch.save()
    
    return Response({
        'message': f'Batch {batch.batch_number} unblocked successfully',
        'batch': BatchDetailSerializer(batch).data
    })


@api_view(['GET'])
@permission_classes([IsManager])
def expired_batches_view(request):
    """List all expired batches"""
    batches = Batch.objects.filter(
        expiry_date__lt=timezone.now().date(),
        quantity__gt=0
    ).select_related('medicine', 'supplier')
    
    serializer = BatchListSerializer(batches, many=True)
    
    total_value = sum(
        batch.quantity * batch.purchase_price
        for batch in batches
    )
    
    return Response({
        'count': batches.count(),
        'total_value': float(total_value),
        'batches': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsManager])
def near_expiry_batches_view(request):
    """List batches nearing expiry (within 90 days)"""
    days = int(request.query_params.get('days', 90))
    near_date = timezone.now().date() + timedelta(days=days)
    
    batches = Batch.objects.filter(
        expiry_date__lte=near_date,
        expiry_date__gt=timezone.now().date(),
        quantity__gt=0
    ).select_related('medicine', 'supplier').order_by('expiry_date')
    
    serializer = BatchListSerializer(batches, many=True)
    
    return Response({
        'count': batches.count(),
        'days_threshold': days,
        'batches': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsManager])
def writeoff_expired_batch(request, pk):
    """Write off expired batch stock"""
    try:
        batch = Batch.objects.get(pk=pk)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if not batch.is_expired:
        return Response(
            {'error': 'Only expired batches can be written off'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if batch.quantity == 0:
        return Response(
            {'error': 'Batch already has zero quantity'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from django.db import transaction
    
    with transaction.atomic():
        previous_quantity = batch.quantity
        reason = request.data.get('reason', f'Expired on {batch.expiry_date}')
        
        # Create stock movement
        MedicineStockMovement.objects.create(
            medicine=batch.medicine,
            batch=batch,
            movement_type='expiry_writeoff',
            quantity=-previous_quantity,
            previous_quantity=previous_quantity,
            new_quantity=0,
            reason=reason,
            performed_by=request.user
        )
        
        # Update batch
        batch.quantity = 0
        batch.save()
    
    return Response({
        'message': f'Batch {batch.batch_number} written off successfully',
        'quantity_written_off': previous_quantity,
        'batch': BatchDetailSerializer(batch).data
    })


# ============================================================================
# STOCK RECEIVING VIEWS
# ============================================================================

class StockReceivingListView(generics.ListAPIView):
    """List all stock receivings"""
    serializer_class = StockReceivingListSerializer
    permission_classes = [IsManager]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['receiving_number', 'supplier__name', 'supplier_invoice_number']
    ordering = ['-received_date']
    
    def get_queryset(self):
        queryset = StockReceiving.objects.select_related('supplier', 'received_by').all()
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class StockReceivingCreateView(generics.CreateAPIView):
    """Create stock receiving"""
    serializer_class = StockReceivingCreateSerializer
    permission_classes = [IsManager]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receiving = serializer.save()
        
        detail_serializer = StockReceivingDetailSerializer(receiving)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class StockReceivingDetailView(generics.RetrieveAPIView):
    """Retrieve stock receiving details"""
    queryset = StockReceiving.objects.prefetch_related('items__medicine', 'items__batch').all()
    serializer_class = StockReceivingDetailSerializer
    permission_classes = [IsManager]


# ============================================================================
# PHARMACY SALE VIEWS
# ============================================================================

class PharmacySaleListView(generics.ListAPIView):
    """List all pharmacy sales"""
    serializer_class = PharmacySaleListSerializer
    permission_classes = [IsCashier]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = PharmacySale.objects.select_related('dispenser').all()
        
        # Date filters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            from datetime import datetime, timedelta
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(created_at__lt=end_datetime)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Cashier filter
        user = self.request.user
        if user.is_cashier and not (user.is_admin or user.is_manager):
            queryset = queryset.filter(dispenser=user)
        
        return queryset


class PharmacySaleCreateView(generics.CreateAPIView):
    """Create pharmacy sale with FEFO"""
    serializer_class = PharmacySaleCreateSerializer
    permission_classes = [IsCashier]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.save()
        
        detail_serializer = PharmacySaleDetailSerializer(sale)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class PharmacySaleDetailView(generics.RetrieveAPIView):
    """Retrieve pharmacy sale details"""
    queryset = PharmacySale.objects.prefetch_related('items__medicine', 'items__batch').all()
    serializer_class = PharmacySaleDetailSerializer
    permission_classes = [IsCashier]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_cashier and not (user.is_admin or user.is_manager):
            queryset = queryset.filter(dispenser=user)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsManager])
def void_pharmacy_sale(request, pk):
    """Void a sale and reverse stock"""
    try:
        sale = PharmacySale.objects.get(pk=pk)
    except PharmacySale.DoesNotExist:
        return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if sale.status == 'voided':
        return Response(
            {'error': 'Sale is already voided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    void_reason = request.data.get('reason', '')
    if not void_reason:
        return Response(
            {'error': 'Void reason is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from django.db import transaction
    
    with transaction.atomic():
        # Reverse stock for each item
        for item in sale.items.all():
            batch = item.batch
            previous_quantity = batch.quantity
            batch.quantity += item.quantity
            batch.save()
            
            # Create stock movement
            MedicineStockMovement.objects.create(
                medicine=item.medicine,
                batch=batch,
                movement_type='return',
                quantity=item.quantity,
                previous_quantity=previous_quantity,
                new_quantity=batch.quantity,
                reference_number=f"VOID-{sale.invoice_number}",
                sale=sale,
                reason=f"Sale voided: {void_reason}",
                performed_by=request.user
            )
            
            # If controlled drug, reverse register
            if item.medicine.is_controlled_drug:
                ControlledDrugRegister.objects.create(
                    medicine=item.medicine,
                    batch=batch,
                    transaction_type='adjustment',
                    quantity=item.quantity,
                    balance=batch.quantity,
                    sale=sale,
                    dispensed_by=request.user,
                    notes=f"Sale voided: {void_reason}"
                )
        
        # Update sale status
        sale.status = 'voided'
        sale.voided_by = request.user
        sale.voided_at = timezone.now()
        sale.void_reason = void_reason
        sale.save()
    
    return Response({
        'message': 'Sale voided successfully',
        'sale': PharmacySaleDetailSerializer(sale).data
    })


# ============================================================================
# REPORTS & STATISTICS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsManager])
def pharmacy_dashboard_stats(request):
    """Dashboard statistics for pharmacy"""
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Sales stats
    sales_today = PharmacySale.objects.filter(
        status='completed',
        created_at__date=today
    ).aggregate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    sales_month = PharmacySale.objects.filter(
        status='completed',
        created_at__gte=thirty_days_ago
    ).aggregate(
        count=Count('id'),
        revenue=Sum('total')
    )
    
    # Stock stats
    total_medicines = Medicine.objects.filter(is_active=True).count()
    low_stock_medicines = [
        m for m in Medicine.objects.filter(is_active=True)
        if m.total_stock <= m.min_stock_level
    ]
    
    # Expiry stats
    expired_batches = Batch.objects.filter(
        expiry_date__lt=today,
        quantity__gt=0
    ).count()
    
    near_expiry_batches = Batch.objects.filter(
        expiry_date__lte=today + timedelta(days=90),
        expiry_date__gt=today,
        quantity__gt=0
    ).count()
    
    # Prescription stats
    prescriptions_today = PharmacySale.objects.filter(
        created_at__date=today,
        has_prescription=True,
        status='completed'
    ).count()
    
    return Response({
        'today': {
            'sales': sales_today['count'] or 0,
            'revenue': float(sales_today['revenue'] or 0),
            'prescriptions': prescriptions_today
        },
        'this_month': {
            'sales': sales_month['count'] or 0,
            'revenue': float(sales_month['revenue'] or 0)
        },
        'inventory': {
            'total_medicines': total_medicines,
            'low_stock': len(low_stock_medicines),
            'expired_batches': expired_batches,
            'near_expiry_batches': near_expiry_batches
        }
    })


@api_view(['GET'])
@permission_classes([IsManager])
def controlled_drugs_report(request):
    """Report on controlled drug movements"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    queryset = ControlledDrugRegister.objects.select_related(
        'medicine', 'batch', 'dispensed_by'
    ).all()
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        from datetime import datetime, timedelta
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    entries = queryset.order_by('-created_at')
    
    data = [{
        'id': entry.id,
        'medicine': entry.medicine.name,
        'batch_number': entry.batch.batch_number,
        'transaction_type': entry.transaction_type,
        'quantity': entry.quantity,
        'balance': entry.balance,
        'customer_name': entry.customer_name,
        'prescription_number': entry.prescription_number,
        'prescriber_name': entry.prescriber_name,
        'dispensed_by': entry.dispensed_by.username,
        'date': entry.created_at.isoformat()
    } for entry in entries]
    
    return Response({
        'count': len(data),
        'entries': data
    })


@api_view(['GET'])
@permission_classes([IsManager])
def stock_movement_report(request):
    """Stock movement history"""
    medicine_id = request.query_params.get('medicine')
    batch_id = request.query_params.get('batch')
    movement_type = request.query_params.get('movement_type')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    queryset = MedicineStockMovement.objects.select_related(
        'medicine', 'batch', 'performed_by'
    ).all()
    
    if medicine_id:
        queryset = queryset.filter(medicine_id=medicine_id)
    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)
    if movement_type:
        queryset = queryset.filter(movement_type=movement_type)
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        from datetime import datetime, timedelta
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        queryset = queryset.filter(created_at__lt=end_datetime)
    
    serializer = MedicineStockMovementSerializer(queryset, many=True)
    
    return Response({
        'count': queryset.count(),
        'movements': serializer.data
    })