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
    ProductListView,
    ProductCreateView,
    ProductDetailView,
    ProductSearchView,
    LowStockProductsView,
    BulkProductUploadView,
    product_stats_view,
    # Sales views
    SaleListView,
    SaleCreateView,
    SaleDetailView,
    sales_stats_view,
    top_selling_products_view,
    cancel_sale_view,
    # Inventory views
    SupplierListCreateView,
    SupplierDetailView,
    StockMovementListView,
    StockAdjustmentView,
    PurchaseOrderListView,
    PurchaseOrderCreateView,
    PurchaseOrderDetailView,
    receive_purchase_order,
    cancel_purchase_order,
    StockAlertListView,
    inventory_stats_view,
    # Reports views
    sales_report_view,
    product_performance_report_view,
    cashier_performance_report_view,
    inventory_report_view,
    dashboard_stats_view,
    export_sales_report_csv,
    # Bulk product views
    create_bulk_parent_product,
    create_child_products_from_parent,
    parent_product_children,
    update_parent_stock,
    product_stock_info,
    # Password Reset
    reset_user_password,
    change_own_password,
    # Certificates
    get_qz_certificate, 
    sign_qz_data,
    # 
    deactivate_product,
    reactivate_product,
    force_delete_product,
    # Medicine views
    MedicineListView,
    MedicineCreateView,
    MedicineDetailView,
    deactivate_medicine,
    reactivate_medicine,
    
    # Batch views
    BatchListView,
    BatchDetailView,
    block_batch,
    unblock_batch,
    expired_batches_view,
    near_expiry_batches_view,
    writeoff_expired_batch,
    
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
    
    # Stores
    path('stores/', StoreListCreateView.as_view(), name='store_list_create'),
    path('stores/<int:pk>/', StoreDetailView.as_view(), name='store_detail'),
    path('stores/default/', get_default_store, name='get_default_store'),
    path('stores/<int:pk>/set-default/', set_default_store, name='set_default_store'),
    path('stores/my-store/', get_user_store, name='get_user_store'),
    
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category_list_create'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category_detail'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/search/', ProductSearchView.as_view(), name='product_search'),
    path('products/low-stock/', LowStockProductsView.as_view(), name='low_stock_products'),
    path('products/bulk-upload/', BulkProductUploadView.as_view(), name='bulk_upload'),
    path('products/stats/', product_stats_view, name='product_stats'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    
    # Sales
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('sales/create/', SaleCreateView.as_view(), name='sale_create'),
    path('sales/stats/', sales_stats_view, name='sales_stats'),
    path('sales/top-products/', top_selling_products_view, name='top_products'),
    path('sales/<int:pk>/', SaleDetailView.as_view(), name='sale_detail'),
    path('sales/<int:pk>/cancel/', cancel_sale_view, name='cancel_sale'),
    
    # Inventory - Suppliers
    path('inventory/suppliers/', SupplierListCreateView.as_view(), name='supplier_list_create'),
    path('inventory/suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier_detail'),
    
    # Inventory - Stock Movements
    path('inventory/stock-movements/', StockMovementListView.as_view(), name='stock_movement_list'),
    path('inventory/stock-adjustment/', StockAdjustmentView.as_view(), name='stock_adjustment'),
    
    # Inventory - Purchase Orders
    path('inventory/purchase-orders/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('inventory/purchase-orders/create/', PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('inventory/purchase-orders/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('inventory/purchase-orders/<int:pk>/receive/', receive_purchase_order, name='receive_purchase_order'),
    path('inventory/purchase-orders/<int:pk>/cancel/', cancel_purchase_order, name='cancel_purchase_order'),
    
    # Inventory - Alerts & Stats
    path('inventory/alerts/', StockAlertListView.as_view(), name='stock_alert_list'),
    path('inventory/stats/', inventory_stats_view, name='inventory_stats'),
    
    # Reports
    path('reports/sales/', sales_report_view, name='sales_report'),
    path('reports/products/', product_performance_report_view, name='product_performance'),
    path('reports/cashiers/', cashier_performance_report_view, name='cashier_performance'),
    path('reports/inventory/', inventory_report_view, name='inventory_report'),
    path('reports/dashboard/', dashboard_stats_view, name='dashboard_stats'),
    path('reports/export/sales/', export_sales_report_csv, name='export_sales_csv'),
    
    # Bulk Product Management
    path('products/bulk/create-parent/', create_bulk_parent_product, name='create_parent_product'),
    path('products/bulk/create-children/', create_child_products_from_parent, name='create_child_products'),
    path('products/bulk/parent/<int:parent_id>/children/', parent_product_children, name='parent_children'),
    path('products/bulk/parent/<int:parent_id>/update-stock/', update_parent_stock, name='update_parent_stock'),
    path('products/<int:product_id>/stock-info/', product_stock_info, name='product_stock_info'),
    
    # Password Management
    path('users/<int:pk>/reset-password/', reset_user_password, name='reset_user_password'),
    path('users/change-password/', change_own_password, name='change_own_password'),
    
    # Certificate sign
    path('qz/certificate/', get_qz_certificate, name='qz_certificate'),
    path('qz/sign/', sign_qz_data, name='qz_sign'),
    
    #
    path('products/<int:pk>/deactivate/', deactivate_product, name='deactivate_product'),
    path('products/<int:pk>/reactivate/', reactivate_product, name='reactivate_product'),
    path('products/<int:pk>/force-delete/', force_delete_product, name='force_delete_product'),
    
    # ===== MEDICINE MANAGEMENT =====
    path('medicines/', MedicineListView.as_view(), name='medicine_list'),
    path('medicines/create/', MedicineCreateView.as_view(), name='medicine_create'),
    path('medicines/<int:pk>/', MedicineDetailView.as_view(), name='medicine_detail'),
    path('medicines/<int:pk>/deactivate/', deactivate_medicine, name='deactivate_medicine'),
    path('medicines/<int:pk>/reactivate/', reactivate_medicine, name='reactivate_medicine'),
    
    # ===== BATCH MANAGEMENT =====
    path('batches/', BatchListView.as_view(), name='batch_list'),
    path('batches/<int:pk>/', BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/block/', block_batch, name='block_batch'),
    path('batches/<int:pk>/unblock/', unblock_batch, name='unblock_batch'),
    path('batches/<int:pk>/writeoff/', writeoff_expired_batch, name='writeoff_batch'),
    path('batches/expired/', expired_batches_view, name='expired_batches'),
    path('batches/near-expiry/', near_expiry_batches_view, name='near_expiry_batches'),
    
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