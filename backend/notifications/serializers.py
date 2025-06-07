# notifications/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, UserNotificationSettings, BlockedContact

# 假设 education.serializers 提供了用户基本信息，如果您的 User 模型在 education 应用中
# from education.serializers import StudentSerializer, TeacherSerializer # 这些可能过于详细，创建一个更基础的

User = get_user_model()


class BasicUserSerializer(serializers.ModelSerializer):
    """
    用于发送者/接收者信息的极简序列化器。
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'role']  # 确保 User 模型有 'name' 字段


class NotificationSerializer(serializers.ModelSerializer):
    sender_info = BasicUserSerializer(source='sender', read_only=True)
    recipient_info = BasicUserSerializer(source='recipient', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_info', 'sender', 'sender_info',
            'type', 'type_display',
            'title', 'content', 'timestamp', 'is_read', 'read_at',
            'content_type', 'object_id',
            'can_recipient_delete', 'can_recipient_reply',
            'parent_notification', 'data'
        ]
        # --- 主要修改在这里 ---
        read_only_fields = [
            'id', 'recipient_info', 'sender_info',
            'type_display',  # type_display 本身就是只读的
            'timestamp', 'read_at', 'content_type', 'object_id',
            'type'  # <-- 新增此行，将 type 字段在反序列化（输入）时设为只读
        ]
        # --------------------

        extra_kwargs = {
            # recipient 字段也应该是只写的，因为它在视图中处理，而不是直接从请求数据中完整解析
            'recipient': {'write_only': True, 'required': False},
            'sender': {'write_only': True, 'required': False},
        }

    # create 方法保持不变
    def create(self, validated_data):
        notification_type = validated_data.get('type')  # 此处获取到的 type 将是后端在 save() 时传入的
        recipient = validated_data.get('recipient')
        sender = validated_data.get('sender')
        recipient_role = recipient.role if recipient else None

        if notification_type == 'private_message':
            validated_data['can_recipient_reply'] = True
            if recipient_role == 'student':
                if sender and sender.role in ['teacher', 'admin', 'superadmin']:
                    validated_data['can_recipient_delete'] = False
                else:
                    validated_data['can_recipient_delete'] = True
        elif notification_type in ['assignment_new', 'assignment_graded', 'course_change', 'class_change',
                                   'system_announcement']:
            validated_data['can_recipient_delete'] = False
            validated_data['can_recipient_reply'] = False
        elif notification_type in ['forum_reply', 'forum_like_summary']:
            validated_data['can_recipient_delete'] = True
            validated_data['can_recipient_reply'] = False

        return super().create(validated_data)


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSettings
        fields = '__all__'
        read_only_fields = ['user']  # user 字段应只读，通过 perform_create 设置


class BlockedContactSerializer(serializers.ModelSerializer):
    blocker_username = serializers.CharField(source='blocker.username', read_only=True)
    blocked_user_username = serializers.CharField(source='blocked_user.username', read_only=True)
    blocked_user_details = BasicUserSerializer(source='blocked_user', read_only=True)  # 显示被屏蔽用户的基本信息

    class Meta:
        model = BlockedContact
        fields = ['id', 'blocker', 'blocker_username', 'blocked_user', 'blocked_user_username', 'blocked_user_details',
                  'timestamp']
        read_only_fields = ['id', 'blocker', 'blocker_username', 'blocked_user_username', 'blocked_user_details',
                            'timestamp']
        extra_kwargs = {
            'blocked_user': {'write_only': True}  # 创建时只接受 blocked_user 的 ID
        }
