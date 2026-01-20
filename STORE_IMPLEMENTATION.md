# Store Management Implementation

## Overview
Enhanced the Store model with default store functionality and admin/manager capabilities for managing multiple stores.

## Changes Made

### 1. Enhanced Store Model (`core/models.py`)
- Added `is_default` field to mark default store
- Added `is_active` field for store status
- Added contact fields: `address`, `phone`, `email`
- Added `created_by` and `updated_at` fields for audit trail
- Implemented `get_default_store()` class method that creates a default store if none exists
- Added validation to ensure only one default store exists

### 2. Store Admin (`core/admin.py`)
- Registered Store model with custom admin interface
- Added list displays, filters, and search capabilities
- Implemented permission-based queryset filtering
- Only superusers and store creators/managers can access stores

### 3. Store API Views (`core/views.py`)
- `StoreListCreateView`: List all stores (Admin only) or create new store
- `StoreDetailView`: Retrieve, update, delete store (Admin only)
- `get_default_store`: Get the default store
- `set_default_store`: Set a store as default (Admin only)
- `get_user_store`: Get current user's store (assigns default if none)

### 4. Store Serializers (`core/serializers.py`)
- `StoreSerializer`: Basic store serialization with read-only fields
- `StoreCreateSerializer`: Store creation with admin validation

### 5. URL Endpoints (`core/urls.py`)
- `/stores/` - List/Create stores
- `/stores/<id>/` - Get/Update/Delete store
- `/stores/default/` - Get default store
- `/stores/<id>/set-default/` - Set store as default
- `/stores/my-store/` - Get current user's store

### 6. Management Command
- `setup_default_store`: Command to set up default store and assign users

## API Usage

### Create a New Store (Admin only)
```http
POST /api/stores/
{
    "name": "Main Branch",
    "description": "Main pharmacy branch",
    "address": "123 Main St, City",
    "phone": "+1234567890",
    "email": "main@pharmacy.com",
    "is_active": true
}
```

### Get Default Store
```http
GET /api/stores/default/
```

### Set Store as Default (Admin only)
```http
POST /api/stores/1/set-default/
```

### Get Current User's Store
```http
GET /api/stores/my-store/
```

## Features

1. **Default Store**: Automatically created and assigned to users without stores
2. **Admin Control**: Only admins can create, modify, and manage stores
3. **Single Default**: Only one store can be marked as default at a time
4. **Audit Trail**: Tracks who created each store and when
5. **Auto-assignment**: Users without stores are automatically assigned to default store

## Security
- Store creation and management restricted to Admin users only
- Users can only access stores they're assigned to (non-superusers)
- Default store setting restricted to admins
- Proper permission checks throughout the system

## Setup
Run the following command to set up the default store:
```bash
python manage.py setup_default_store
```