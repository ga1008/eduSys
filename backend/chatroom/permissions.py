# backend/chatroom/permissions.py

from rest_framework.permissions import BasePermission
from .models import ChatRoomMember


class IsChatRoomAdmin(BasePermission):
    """
    允许对聊天室有管理员权限的用户进行操作。
    """
    message = '您不是此聊天室的管理员。'

    def has_permission(self, request, view):
        # 先确保用户已登录
        if not request.user or not request.user.is_authenticated:
            return False

        # 从 URL 获取 room_id
        room_id = view.kwargs.get('room_pk') or view.kwargs.get('pk')
        if not room_id:
            return False  # 如果没有 room_id，则无法判断权限

        # 检查用户是否是该聊天室的管理员
        try:
            member = ChatRoomMember.objects.get(room_id=room_id, user=request.user)
            return member.role == 'admin' and member.is_active
        except ChatRoomMember.DoesNotExist:
            return False
