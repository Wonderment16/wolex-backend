from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    def has_object_permission(sellf, request, view, obj):
        return obj.user == request.user
    