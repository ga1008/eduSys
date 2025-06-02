from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """超级管理员权限"""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'superadmin'
        )


class IsAdmin(BasePermission):
    """普通管理员权限（包含超级管理员）"""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ['admin', 'superadmin']
        )


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'teacher'
        )
