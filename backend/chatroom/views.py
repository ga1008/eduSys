# backend/chatroom/views.py

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import ChatRoom, ChatMessage, ChatRoomMember
from .serializers import ChatRoomSerializer, ChatMessageSerializer, ChatRoomMemberSerializer
from .permissions import IsChatRoomAdmin
from django.shortcuts import get_object_or_404
from .tasks import process_chat_file_upload  # 导入Celery任务


class ChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供聊天室列表和详情的只读视图。
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 用户只能看到自己所在的聊天室
        user = self.request.user
        member_of_rooms = ChatRoomMember.objects.filter(user=user, is_active=True).values_list('room_id', flat=True)
        return ChatRoom.objects.filter(id__in=member_of_rooms)

    @action(detail=True, methods=['get'], url_path='messages')
    def list_messages(self, request, pk=None):
        """
        获取聊天室的历史消息（分页）。
        GET /api/chatrooms/{pk}/messages/
        """
        room = self.get_object()
        # 验证当前用户是否是成员
        if not ChatRoomMember.objects.filter(room=room, user=request.user, is_active=True).exists():
            return Response({"detail": "您不是该聊天室成员。"}, status=status.HTTP_403_FORBIDDEN)

        messages = ChatMessage.objects.filter(room=room, is_deleted=False).order_by('-timestamp')

        # 分页处理
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = ChatMessageSerializer(page, many=True)
            # 注意：分页结果是倒序的，前端需要反转来正确显示
            return self.get_paginated_response(serializer.data)

        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='members')
    def list_members(self, request, pk=None):
        """
        获取聊天室的成员列表。
        GET /api/chatrooms/{pk}/members/
        """
        room = self.get_object()
        if not ChatRoomMember.objects.filter(room=room, user=request.user, is_active=True).exists():
            return Response({"detail": "您不是该聊天室成员。"}, status=status.HTTP_403_FORBIDDEN)

        members = ChatRoomMember.objects.filter(room=room, is_active=True).select_related('user')
        serializer = ChatRoomMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser], url_path='upload')
    def upload_file(self, request, pk=None):
        """
        处理文件上传的专用API。
        POST /api/chatrooms/{pk}/upload/
        """
        room = self.get_object()
        user = request.user
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response({"detail": "未提供文件。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = ChatRoomMember.objects.get(room=room, user=user, is_active=True)
        except ChatRoomMember.DoesNotExist:
            return Response({"detail": "您不是该聊天室成员或已被移出。"}, status=status.HTTP_403_FORBIDDEN)

        # 1. 先在数据库中创建一个消息占位符
        # 根据文件类型判断 message_type
        content_type = file_obj.content_type
        if 'image' in content_type:
            msg_type = 'image'
        elif 'video' in content_type:
            msg_type = 'video'
        else:
            msg_type = 'file'

        message = ChatMessage.objects.create(
            room=room,
            author=member,
            message_type=msg_type,
            content=f"正在上传文件: {file_obj.name}...",
            file_original_name=file_obj.name
        )

        # 2. 调用 Celery 任务处理文件
        # 为了传递文件内容，我们需要先读取它
        file_content = file_obj.read()
        process_chat_file_upload.delay(message.id, list(file_content), file_obj.name, content_type)

        # 3. 立即返回响应，告知前端上传已开始
        return Response({"detail": "文件上传处理中...", "message_id": message.id}, status=status.HTTP_202_ACCEPTED)


class ChatRoomAdminViewSet(viewsets.ViewSet):
    """
    管理聊天室的各种操作，需要管理员权限。
    """
    permission_classes = [IsAuthenticated, IsChatRoomAdmin]

    def partial_update(self, request, pk=None):
        """
        更新聊天室设置（如：全员禁言）。
        PATCH /api/chatrooms-admin/{pk}/
        """
        room = get_object_or_404(ChatRoom, pk=pk)
        serializer = ChatRoomSerializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # TODO: 可以在这里广播一个系统消息通知设置已变更
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='members/(?P<member_id>\d+)/role')
    def set_member_role(self, request, pk=None, member_id=None):
        """
        设置或取消成员的管理员身份。
        POST /api/chatrooms-admin/{pk}/members/{member_id}/role/  - body: {"role": "admin/member"}
        """
        member = get_object_or_404(ChatRoomMember, pk=member_id, room_id=pk)
        new_role = request.data.get('role')

        if new_role not in ['admin', 'member']:
            return Response({"detail": "无效的角色。"}, status=status.HTTP_400_BAD_REQUEST)

        # 不能修改教师的管理员角色
        if member.user.role == 'teacher':
            return Response({"detail": "不能修改教师的管理员状态。"}, status=status.HTTP_403_FORBIDDEN)

        member.role = new_role
        member.save()
        # TODO: 广播系统消息
        return Response(ChatRoomMemberSerializer(member).data)

    @action(detail=True, methods=['post'], url_path='members/(?P<member_id>\d+)/kick')
    def kick_member(self, request, pk=None, member_id=None):
        """
        将成员踢出聊天室。
        POST /api/chatrooms-admin/{pk}/members/{member_id}/kick/
        """
        member = get_object_or_404(ChatRoomMember, pk=member_id, room_id=pk)

        # 检查权限，不能踢教师或同级/上级管理员
        if member.user.role == 'teacher' or member.role == 'admin':
            return Response({"detail": "不能移除教师或其他管理员。"}, status=status.HTTP_403_FORBIDDEN)

        member.is_active = False
        member.save()
        # TODO: 广播系统消息
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['delete'], url_path='messages/(?P<message_id>\d+)')
    def delete_message(self, request, pk=None, message_id=None):
        """
        管理员删除任何人的消息。
        DELETE /api/chatrooms-admin/{pk}/messages/{message_id}/
        """
        message = get_object_or_404(ChatMessage, pk=message_id, room_id=pk)
        message.is_deleted = True
        message.content = "[该消息已被管理员撤回]"
        message.save()
        # TODO: 广播消息删除事件
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatRoomMemberSelfViewSet(viewsets.ViewSet):
    """
    用于成员自己操作的接口，如修改自己的昵称。
    """
    permission_classes = [IsAuthenticated]

    def partial_update(self, request, pk=None):
        """
        修改我在此聊天室的昵称。
        PATCH /api/chatrooms/{pk}/me/
        """
        room_id = pk
        new_nickname = request.data.get('nickname')
        if not new_nickname:
            return Response({"detail": "昵称不能为空。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            member = ChatRoomMember.objects.get(room_id=room_id, user=request.user)
            member.nickname = new_nickname
            member.save()
            # TODO: 广播昵称修改事件
            return Response(ChatRoomMemberSerializer(member).data)
        except ChatRoomMember.DoesNotExist:
            return Response({"detail": "找不到您的成员信息。"}, status=status.HTTP_404_NOT_FOUND)
