# backend/forum/permissions.py

from rest_framework import permissions
from course.models import TeacherCourseClass


class CanManageForumContent(permissions.BasePermission):
    """
    自定义权限，用于控制帖子和评论的管理权限。
    - 超管可以管理所有内容。
    - 作者可以管理自己的内容。
    - 老师可以管理其所教班级学生发布的内容。
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限对所有人开放（具体可见性在 View 中处理）
        if request.method in permissions.SAFE_METHODS:
            return True

        # 超级管理员拥有所有权限
        if request.user.is_superuser:
            return True

        # 作者拥有管理自己帖子的权限
        if obj.author == request.user:
            return True

        # 如果当前用户是老师，检查对象作者是否是其学生
        if request.user.role == 'teacher':
            # 获取老师所教的所有班级ID
            teacher_class_ids = TeacherCourseClass.objects.filter(teacher=request.user).values_list('class_obj_id',
                                                                                                    flat=True)

            # 检查帖子的作者是否在这些班级中
            if obj.author.role == 'student' and obj.author.class_enrolled_id in teacher_class_ids:
                return True

        return False
