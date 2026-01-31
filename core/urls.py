from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    UserListView,
    UserDetailView,
    CurrentUserView,
    ChangePasswordView,
    RoleListView,
    logout_view,
    # Store views
    StoreListCreateView,
    StoreDetailView,
    get_default_store,
    set_default_store,
    get_user_store,
    # Product views
    CategoryListCreateView,
    CategoryDetailView,
    # Inventory views
    SupplierListCreateView,
    SupplierDetailView,
    # Password Reset
    reset_user_password,
    change_own_password,
    # Certificates
    get_qz_certificate, 
    sign_qz_data,
    # Medicine views
    MedicineListView,
    MedicineCreateView,
    MedicineDetailView,
    deactivate_medicine,
    reactivate_medicine,
    medicine_batches_view,
    
    # Batch views
    BatchListView,
    BatchCreateView,
    batch_stats_view,
    BatchDetailView,
    block_batch,
    unblock_batch,
    expired_batches_view,
    near_expiry_batches_view,
    writeoff_expired_batch,
    adjust_batch_quantity,
    batch_history_view,
    
    # Stock receiving views
    StockReceivingListView,
    StockReceivingCreateView,
    StockReceivingDetailView,
    
    # Pharmacy sale views
    PharmacySaleListView,
    PharmacySaleCreateView,
    PharmacySaleDetailView,
    void_pharmacy_sale,
    
    # Reports
    pharmacy_dashboard_stats,
    controlled_drugs_report,
    stock_movement_report,
    
    ##
    check_setup_status,
    complete_initial_setup,
)

urlpatterns = [
    # Authentication
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # User Management
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/register/', RegisterView.as_view(), name='register'),
    path('users/me/', CurrentUserView.as_view(), name='current_user'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    
    # Roles
    path('roles/', RoleListView.as_view(), name='role_list'),
    
    # Setup endpoints
    path('setup/status/', check_setup_status, name='setup_status'),
    path('setup/complete/', complete_initial_setup, name='complete_setup'), 
    # Stores
    path('stores/', StoreListCreateView.as_view(), name='store_list_create'),
    path('stores/<int:pk>/', StoreDetailView.as_view(), name='store_detail'),
    path('stores/default/', get_default_store, name='get_default_store'),
    path('stores/<int:pk>/set-default/', set_default_store, name='set_default_store'),
    path('stores/my-store/', get_user_store, name='get_user_store'),
    
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # Inventory - Suppliers
    path('inventory/suppliers/', SupplierListCreateView.as_view(), name='supplier_list_create'),
    path('inventory/suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    
    # Password Management
    path('users/<int:pk>/reset-password/', reset_user_password, name='reset_user_password'),
    path('users/change-password/', change_own_password, name='change_own_password'),
    
    # Certificate sign
    path('qz/certificate/', get_qz_certificate, name='qz_certificate'),
    path('qz/sign/', sign_qz_data, name='qz_sign'),
    
    # ===== MEDICINE MANAGEMENT =====
    path('medicines/', MedicineListView.as_view(), name='medicine_list'),
    path('medicines/create/', MedicineCreateView.as_view(), name='medicine_create'),
    path('medicines/<int:pk>/', MedicineDetailView.as_view(), name='medicine_detail'),
    path('medicines/<int:pk>/deactivate/', deactivate_medicine, name='deactivate_medicine'),
    path('medicines/<int:pk>/reactivate/', reactivate_medicine, name='reactivate_medicine'),
    path('medicines/<int:medicine_id>/batches/', medicine_batches_view, name='medicine_batches'),
    
    # ===== BATCH MANAGEMENT =====
    path('batches/', BatchListView.as_view(), name='batch_list'),
    path('batches/create/', BatchCreateView.as_view(), name='batch_create'),
    path('batches/stats/', batch_stats_view, name='batch_stats'),
    path('batches/expired/', expired_batches_view, name='expired_batches'),
    path('batches/near-expiry/', near_expiry_batches_view, name='near_expiry_batches'),
    path('batches/<int:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/block/', block_batch, name='block_batch'),
    path('batches/<int:pk>/unblock/', unblock_batch, name='unblock_batch'),
    path('batches/<int:pk>/writeoff/', writeoff_expired_batch, name='writeoff_batch'),
    path('batches/<int:pk>/adjust/', adjust_batch_quantity, name='adjust_batch_quantity'),
    path('batches/<int:pk>/history/', batch_history_view, name='batch_history'),

    
    # ===== STOCK RECEIVING =====
    path('stock-receiving/', StockReceivingListView.as_view(), name='stock_receiving_list'),
    path('stock-receiving/create/', StockReceivingCreateView.as_view(), name='stock_receiving_create'),
    path('stock-receiving/<int:pk>/', StockReceivingDetailView.as_view(), name='stock_receiving_detail'),
    
    # ===== PHARMACY SALES (DISPENSING) =====
    path('sales/', PharmacySaleListView.as_view(), name='pharmacy_sale_list'),
    path('sales/create/', PharmacySaleCreateView.as_view(), name='pharmacy_sale_create'),
    path('sales/<int:pk>/', PharmacySaleDetailView.as_view(), name='pharmacy_sale_detail'),
    path('sales/<int:pk>/void/', void_pharmacy_sale, name='void_pharmacy_sale'),
    
    # ===== REPORTS & STATISTICS =====
    path('dashboard/', pharmacy_dashboard_stats, name='pharmacy_dashboard'),
    path('reports/controlled-drugs/', controlled_drugs_report, name='controlled_drugs_report'),
    path('reports/stock-movements/', stock_movement_report, name='stock_movement_report'),
]