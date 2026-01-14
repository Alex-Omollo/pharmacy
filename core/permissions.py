from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """Permission check for admin users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsManager(permissions.BasePermission):
    """Permission check for manager users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_manager
        )


class IsCashier(permissions.BasePermission):
    """Permission check for cashier users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.is_manager or request.user.is_cashier
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admins full access, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_admin
    

##