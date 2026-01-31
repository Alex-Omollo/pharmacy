from django.contrib import admin
from .models import (
    Store, Role, User, Category, 
    Medicine, Batch, Supplier,
)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'is_active', 'phone', 'created_at']
    list_filter = ['is_default', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see stores they created or are assigned to
        return qs.filter(created_by=request.user) | qs.filter(users=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'store', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Managers can only see users in their store
        if request.user.is_manager:
            return qs.filter(store=request.user.store)
        return qs.filter(pk=request.user.pk)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'store']
    # search_fields = ['name', 'description']
    # readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(store=request.user.store)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj,store = request.user.store or Store.get_default_store()
        super().save_model(request, obj, form, change)


# Register other models as needed
admin.site.register(Medicine)
admin.site.register(Batch)
admin.site.register(Supplier)
