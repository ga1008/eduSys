from rest_framework import permissions
from rest_framework.permissions import BasePermission

from course.models import Assignment


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'is_superuser', False))


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        # 假设 User 模型有属性 role 或通过组判断
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'role', None) == 'Teacher')


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

    # def has_object_permission(self, request, view, obj):
    #     # 确保学生只能操作自己的数据
    #     if hasattr(obj, 'student'):
    #         return obj.student == request.user
    #     if hasattr(obj, 'user'):
    #         return obj.user == request.user
    #     return False


# 权限类：确保教师只能访问自己的课程
class IsTeacherOrAdmin(permissions.BasePermission):
    """
    超管放行；老师只能操作自己教授的教学班或自己布置的作业
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", "") in {"teacher", "admin", "superadmin"}

    # def has_object_permission(self, request, view, obj):
    #     # 超管直接放行
    #     if request.user.role in ['admin', 'superadmin']:
    #         return True

        # # Homework：布置者或任课教师
        # if isinstance(obj, Homework):
        #     return (
        #         obj.deployer_id == request.user.id or
        #         obj.course_class.teacher_id == request.user.id
        #     )
        #
        # # TeacherCourseClass / Material 等原逻辑
        # if hasattr(obj, 'teacher'):
        #     return obj.teacher_id == request.user.id
        # if hasattr(obj, 'teaching_class'):
        #     return obj.teaching_class.teacher_id == request.user.id
        # return False