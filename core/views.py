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
    User, Role, Category, Supplier, 
    Medicine, Batch, StockReceiving, 
    MedicineStockMovement, PharmacySale, 
    PharmacySaleItem, ControlledDrugRegister, Store
)
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, ChangePasswordSerializer,
    RoleSerializer, StoreSerializer, StoreCreateSerializer, CategorySerializer, SupplierSerializer,
    MedicineListSerializer, MedicineDetailSerializer, MedicineCreateUpdateSerializer, BatchListSerializer,
    BatchDetailSerializer, BatchCreateSerializer, BatchUpdateSerializer, StockReceivingListSerializer,
    StockReceivingDetailSerializer, StockReceivingCreateSerializer, PharmacySaleListSerializer, 
    PharmacySaleDetailSerializer, PharmacySaleCreateSerializer, MedicineStockMovementSerializer, CompleteSetupSerializer
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
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        """Filter categories by user's store"""
        if self.request.user.is_superuser:
            return Category.objects.all()
        return Category.objects.filter(store=self.request.user.store)
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsManager()]
        return [IsCashier()]
    
    def perform_create(self, serializer):
        """Automatically assign store when creating category"""
        user = self.request.user
        store = user.store if user.store else Store.get_default_store()
        
        if not store:
            raise ValidationError('No store available. Please contact administrator')
        
        serializer.save(store=store)

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category (Admin/Manager only for modifications)"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsManager()]
        return [IsCashier()]
         
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
    ordering_fields = ['b_name', 'generic_name', 'selling_price', 'buying_price', 'created_at']
    ordering = ['b_name']
    
    def get_queryset(self):
        queryset = Medicine.objects.select_related('category').prefetch_related('batches')
        
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
        'message': f'Medicine "{medicine.b_name}" deactivated successfully',
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
        'message': f'Medicine "{medicine.b_name}" reactivated successfully',
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
    search_fields = ['batch_number', 'medicine__b_name', 'medicine__generic_name']
    ordering_fields = ['expiry_date', 'received_date', 'quantity']
    ordering = ['expiry_date']
    
    def get_queryset(self):
        queryset = Batch.objects.select_related('medicine', 'supplier').all()
        
        # Filter by medicine
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        
        # Filter by status - use actual database fields, not properties
        status_filter = self.request.query_params.get('status')
        today = timezone.now().date()
        
        if status_filter == 'available':
            # Available: not expired, not blocked, has quantity
            queryset = queryset.filter(
                expiry_date__gt=today,
                is_blocked=False,
                quantity__gt=0
            )
        elif status_filter == 'expired':
            # Expired: expiry date is in the past
            queryset = queryset.filter(expiry_date__lt=today)
        elif status_filter == 'near_expiry':
            # Near expiry: expires within 90 days but not yet expired
            near_date = today + timedelta(days=90)
            queryset = queryset.filter(
                expiry_date__lte=near_date,
                expiry_date__gt=today
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

class BatchCreateView(generics.CreateAPIView):
    """Create new batch"""
    serializer_class = BatchCreateSerializer
    permission_classes = [IsManager]
    
    def perform_create(self, serializer):
        serializer.save(received_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override to provide better error messages"""
        print("Batch Create Request Data:", request.data)  # Debug log
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            print("Validation Errors:", serializer.errors)  # Debug log
            return Response(
                {
                    'error': 'Validation failed',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            {
                'message': 'Batch created successfully',
                'batch': BatchDetailSerializer(serializer.instance).data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

@api_view(['GET'])
@permission_classes([IsManager])
def medicine_batches_view(request, medicine_id):
    """Get all batches for a specific medicine"""
    try:
        medicine = Medicine.objects.get(pk=medicine_id)
    except Medicine.DoesNotExist:
        return Response({'error': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get filter parameters
    status_filter = request.query_params.get('status', 'all')
    
    queryset = medicine.batches.select_related('supplier').all()
    
    if status_filter == 'available':
        queryset = queryset.filter(
            expiry_date__gt=timezone.now().date(),
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
    elif status_filter == 'depleted':
        queryset = queryset.filter(quantity=0)
    
    queryset = queryset.order_by('expiry_date')
    
    serializer = BatchListSerializer(queryset, many=True)
    
    return Response({
        'medicine': {
            'id': medicine.id,
            'name': medicine.b_name,
            'generic_name': medicine.generic_name,
            'total_stock': medicine.total_stock,
        },
        'batches': serializer.data,
        'count': queryset.count()
    })

@api_view(['POST'])
@permission_classes([IsManager])
def adjust_batch_quantity(request, pk):
    """Manually adjust batch quantity (for corrections, damage, etc.)"""
    try:
        batch = Batch.objects.get(pk=pk)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
    
    adjustment_type = request.data.get('adjustment_type')  # 'add', 'remove', 'set'
    quantity = request.data.get('quantity')
    reason = request.data.get('reason', '')
    
    if not adjustment_type or quantity is None:
        return Response(
            {'error': 'adjustment_type and quantity are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        quantity = int(quantity)
    except ValueError:
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not reason.strip():
        return Response({'error': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    from django.db import transaction
    
    with transaction.atomic():
        previous_quantity = batch.quantity
        
        if adjustment_type == 'add':
            new_quantity = previous_quantity + quantity
            movement_quantity = quantity
        elif adjustment_type == 'remove':
            if quantity > previous_quantity:
                return Response(
                    {'error': f'Cannot remove {quantity} units. Only {previous_quantity} available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            new_quantity = previous_quantity - quantity
            movement_quantity = -quantity
        elif adjustment_type == 'set':
            new_quantity = quantity
            movement_quantity = quantity - previous_quantity
        else:
            return Response(
                {'error': 'Invalid adjustment_type. Must be: add, remove, or set'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_quantity < 0:
            return Response({'error': 'Quantity cannot be negative'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update batch
        batch.quantity = new_quantity
        batch.save()
        
        # Create stock movement
        movement = MedicineStockMovement.objects.create(
            medicine=batch.medicine,
            batch=batch,
            movement_type='adjustment',
            quantity=movement_quantity,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reason=reason,
            performed_by=request.user
        )
        
        # If controlled drug, create register entry
        if batch.medicine.is_controlled_drug:
            ControlledDrugRegister.objects.create(
                medicine=batch.medicine,
                batch=batch,
                transaction_type='adjustment',
                quantity=movement_quantity,
                balance=new_quantity,
                dispensed_by=request.user,
                notes=reason
            )
    
    return Response({
        'message': 'Batch quantity adjusted successfully',
        'batch': BatchDetailSerializer(batch).data,
        'movement': MedicineStockMovementSerializer(movement).data
    })

@api_view(['GET'])
@permission_classes([IsManager])
def batch_history_view(request, pk):
    """Get stock movement history for a specific batch"""
    try:
        batch = Batch.objects.get(pk=pk)
    except Batch.DoesNotExist:
        return Response({'error': 'Batch not found'}, status=status.HTTP_404_NOT_FOUND)
    
    movements = MedicineStockMovement.objects.filter(
        batch=batch
    ).select_related('performed_by').order_by('-created_at')
    
    serializer = MedicineStockMovementSerializer(movements, many=True)
    
    return Response({
        'batch': BatchDetailSerializer(batch).data,
        'movements': serializer.data,
        'count': movements.count()
    })

@api_view(['GET'])
@permission_classes([IsManager])
def batch_stats_view(request):
    """Get batch statistics"""
    from django.db.models import Sum, Count, Q
    
    today = timezone.now().date()
    
    # Total batches
    total_batches = Batch.objects.count()
    active_batches = Batch.objects.filter(quantity__gt=0, expiry_date__gt=today, is_blocked=False).count()
    
    # Expired batches
    expired_batches = Batch.objects.filter(expiry_date__lt=today, quantity__gt=0)
    expired_count = expired_batches.count()
    expired_value = sum(batch.quantity * batch.purchase_price for batch in expired_batches)
    
    # Near expiry (30, 60, 90 days)
    near_expiry_30 = Batch.objects.filter(
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gt=today,
        quantity__gt=0
    ).count()
    
    near_expiry_60 = Batch.objects.filter(
        expiry_date__lte=today + timedelta(days=60),
        expiry_date__gt=today,
        quantity__gt=0
    ).count()
    
    near_expiry_90 = Batch.objects.filter(
        expiry_date__lte=today + timedelta(days=90),
        expiry_date__gt=today,
        quantity__gt=0
    ).count()
    
    # Blocked batches
    blocked_batches = Batch.objects.filter(is_blocked=True, quantity__gt=0).count()
    
    # Depleted batches
    depleted_batches = Batch.objects.filter(quantity=0).count()
    
    # Total stock value
    all_batches = Batch.objects.filter(quantity__gt=0, expiry_date__gt=today, is_blocked=False)
    total_stock_value = sum(batch.quantity * batch.purchase_price for batch in all_batches)
    
    return Response({
        'total_batches': total_batches,
        'active_batches': active_batches,
        'depleted_batches': depleted_batches,
        'blocked_batches': blocked_batches,
        'expired': {
            'count': expired_count,
            'value': float(expired_value)
        },
        'near_expiry': {
            '30_days': near_expiry_30,
            '60_days': near_expiry_60,
            '90_days': near_expiry_90
        },
        'total_stock_value': float(total_stock_value)
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