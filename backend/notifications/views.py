# notifications/views.py
from rest_framework import viewsets, status, generics, mixins, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Notification, UserNotificationSettings, BlockedContact
from .serializers import (
    NotificationSerializer,
    UserNotificationSettingsSerializer,
    BlockedContactSerializer,
    BasicUserSerializer  # 用于用户搜索
)

# from .permissions import CanManageOwnNotifications, CanManageSettings, CanManageBlocking # 自定义权限类

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]  # TODO: 替换为更细致的自定义权限

    def get_queryset(self):
        """
        用户只能看到自己的通知。
        """
        user = self.request.user
        base_qs = Notification.objects.filter(recipient=user)

        # 按类型过滤
        notification_type = self.request.query_params.get('type')
        if notification_type:
            base_qs = base_qs.filter(type=notification_type)

        # 按已读/未读状态过滤
        is_read_param = self.request.query_params.get('is_read')
        if is_read_param is not None:
            is_read = is_read_param.lower() == 'true'
            base_qs = base_qs.filter(is_read=is_read)

        return base_qs.select_related('sender', 'recipient', 'content_type', 'parent_notification')

    def perform_create(self, serializer):
        """
        处理发送通知（例如，私信）。系统生成的通知通过信号或直接模型调用创建。
        此方法主要用于用户主动发送私信。
        """
        sender = self.request.user
        recipient_id = self.request.data.get('recipient')  # 前端应传递 recipient 的 ID
        if not recipient_id:
            raise serializers.ValidationError({"recipient": "必须提供接收者ID。"})

        try:
            # 确保 recipient_id 是整数
            recipient_id = int(recipient_id)
            recipient = User.objects.get(id=recipient_id)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"recipient": "接收用户未找到。"})

        # 检查黑名单规则和接收者设置
        settings, _ = UserNotificationSettings.objects.get_or_create(user=recipient)
        if BlockedContact.objects.filter(blocker=recipient, blocked_user=sender).exists():
            raise serializers.ValidationError({
                "detail": "消息无法发送。接收方可能已将您屏蔽或不接收来自您的消息。"
            })

        # 应用接收者的策略
        policy = settings.private_message_policy
        can_send = False
        if policy == 'everyone':
            can_send = True
        elif policy == 'teachers_staff_only' and recipient.role == 'student' and sender.role in ['teacher', 'admin',
                                                                                                 'superadmin']:
            can_send = True
        elif policy == 'staff_only' and recipient.role == 'teacher' and sender.role in ['admin', 'superadmin']:
            can_send = True
        elif policy == 'superadmin_only' and sender.role == 'superadmin':
            can_send = True
        elif policy == 'none' and sender.role == 'superadmin':  # 超级管理员可以覆盖 'none' 策略发送重要消息
            can_send = True
        # TODO: 实现 'contacts_only' 逻辑

        if not can_send:
            raise serializers.ValidationError({"detail": "接收者当前不接收来自您的消息。"})

        # 根据角色和类型设置 can_recipient_delete (此逻辑也可在序列化器中完成)
        can_delete = True
        if recipient.role == 'student' and sender.role in ['teacher', 'admin', 'superadmin']:
            can_delete = False  # 学生不能删除来自教职工的私信

        title = self.request.data.get('title', f"来自 {sender.username} 的消息")

        serializer.save(
            sender=sender,
            recipient=recipient,
            type='private_message',  # 此端点用于发送私信
            title=title,
            can_recipient_delete=can_delete,
            can_recipient_reply=True  # 私信通常可以回复
        )

    @action(detail=False, methods=['post'], url_path='mark-all-as-read')
    def mark_all_as_read(self, request):
        # 将当前用户的所有未读通知标记为已读
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        # 将指定ID的通知标记为已读
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        return Response(NotificationSerializer(notification, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='mark-unread')
    def mark_unread(self, request, pk=None):
        # 将指定ID的通知标记为未读
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_unread()
        return Response(NotificationSerializer(notification, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        # 获取当前用户的未读通知数量
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})

    def destroy(self, request, *args, **kwargs):
        # 删除通知
        notification = self.get_object()  # get_object 会基于 get_queryset 进一步筛选，确保是当前用户的
        if not notification.can_recipient_delete:
            return Response({"detail": "此通知不能被删除。"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='reply')
    def reply_to_notification(self, request, pk=None):
        # 回复通知
        parent_notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

        if not parent_notification.can_recipient_reply or parent_notification.sender is None:
            return Response({"detail": "不能回复此通知。"}, status=status.HTTP_400_BAD_REQUEST)

        content = request.data.get('content')
        if not content:
            raise serializers.ValidationError({"content": "回复内容不能为空。"})

        # 创建新通知作为回复
        new_recipient = parent_notification.sender
        current_user_as_sender = request.user

        # 检查针对 new_recipient 的屏蔽和策略 (与 perform_create 中类似)
        settings, _ = UserNotificationSettings.objects.get_or_create(user=new_recipient)
        if BlockedContact.objects.filter(blocker=new_recipient, blocked_user=current_user_as_sender).exists():
            raise serializers.ValidationError({"detail": "您的回复无法发送。"})
        # 此处应添加完整的策略检查逻辑...

        # 确定回复消息的 can_recipient_delete 状态
        can_delete_reply = True
        if new_recipient.role == 'student' and current_user_as_sender.role in ['teacher', 'admin', 'superadmin']:
            can_delete_reply = False

        reply_notification_data = {
            'recipient': new_recipient.id,
            'sender': current_user_as_sender.id,  # 当前用户是发送者
            'type': 'private_message',  # 回复也是私信
            'title': f"回复: {parent_notification.title}" if parent_notification.title else "回复消息",
            'content': content,
            'parent_notification': parent_notification.id,
            'can_recipient_delete': can_delete_reply,
            'can_recipient_reply': True  # 回复通常也可以被再次回复
        }
        # 注意：在NotificationSerializer的create方法中，recipient和sender字段通常是从validated_data中获取对象
        # 如果直接传递ID，需要在序列化器的create方法中处理ID到对象的转换，或者在视图中先获取对象。
        # 为简化，这里假设序列化器能处理ID，或在实例化时已处理。
        # 更稳妥的做法是：
        # validated_data['recipient_id'] = new_recipient.id
        # serializer = self.get_serializer(data=reply_notification_data)

        # 直接创建实例并保存，因为大部分字段已知
        new_notification = Notification.objects.create(
            recipient=new_recipient,
            sender=current_user_as_sender,
            type='private_message',
            title=reply_notification_data['title'],
            content=reply_notification_data['content'],
            parent_notification=parent_notification,
            can_recipient_delete=can_delete_reply,
            can_recipient_reply=True
        )

        # 如果原消息未读，则将其标记为已读
        if not parent_notification.is_read:
            parent_notification.mark_as_read()

        return Response(self.get_serializer(new_notification).data, status=status.HTTP_201_CREATED)


class UserNotificationSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationSettingsSerializer
    permission_classes = [IsAuthenticated]  # TODO: 添加自定义权限，如 CanManageOwnSettings

    def get_object(self):
        # 获取或创建当前用户的通知设置
        obj, created = UserNotificationSettings.objects.get_or_create(user=self.request.user)
        return obj

    def perform_update(self, serializer):
        # 此处可添加基于角色的设置验证
        user_role = self.request.user.role
        policy = serializer.validated_data.get('private_message_policy')

        if user_role == 'student':
            if policy in ['staff_only', 'superadmin_only']:  # 学生不能设置这些限制性策略
                raise serializers.ValidationError({"private_message_policy": "学生不能设置此策略。"})
        # 教师和超级管理员可以为自己设置任何策略
        serializer.save()


class BlockedContactViewSet(viewsets.ModelViewSet):
    serializer_class = BlockedContactSerializer
    permission_classes = [IsAuthenticated]  # TODO: 添加自定义权限，如 CanManageBlocking

    def get_queryset(self):
        # 用户只能查看自己的黑名单
        return BlockedContact.objects.filter(blocker=self.request.user).select_related('blocked_user')

    def perform_create(self, serializer):
        # 创建黑名单条目
        blocked_user_id = self.request.data.get('blocked_user')  # 前端应传递 blocked_user 的 ID
        if not blocked_user_id:
            raise serializers.ValidationError({"blocked_user": "必须提供要屏蔽的用户ID。"})
        try:
            blocked_user = User.objects.get(id=blocked_user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"blocked_user": "要屏蔽的用户未找到。"})

        # 规则检查
        if blocked_user.role == 'superadmin' and self.request.user.role != 'superadmin':
            raise serializers.ValidationError({"detail": "您不能屏蔽超级管理员。"})
        if self.request.user.role == 'student' and blocked_user.role in ['teacher', 'admin', 'superadmin']:
            raise serializers.ValidationError({"detail": "学生不能屏蔽教职工。"})
        if self.request.user.role == 'teacher' and blocked_user.role in ['admin', 'superadmin']:
            raise serializers.ValidationError({"detail": "教师不能屏蔽管理员。"})
        if self.request.user == blocked_user:
            raise serializers.ValidationError({"detail": "您不能屏蔽自己。"})

        # 检查是否已存在
        if BlockedContact.objects.filter(blocker=self.request.user, blocked_user=blocked_user).exists():
            raise serializers.ValidationError({"detail": "该用户已在您的黑名单中。"})

        serializer.save(blocker=self.request.user, blocked_user=blocked_user)

    # destroy 方法 (用于取消屏蔽) 继承自 ModelViewSet


# --- 用于消息发送时搜索用户的API ---
class UserSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BasicUserSerializer  # 或更详细的序列化器
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).exclude(is_active=False)  # 排除自己和非活动用户
        search_term = self.request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(
                Q(username__icontains=search_term) |
                Q(name__icontains=search_term) |  # 假设 User 模型有 name 字段
                Q(email__icontains=search_term)
            )
        # 不在此处过滤已被当前用户屏蔽的人，因为搜索时可能仍希望看到他们（但发送消息时会失败）
        # 也不在此处过滤那些设置了不接收私信的人，发送时再判断
        return queryset.order_by('username')[:20]  # 限制结果数量，防止性能问题
