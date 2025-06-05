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
    type_display = serializers.CharField(source='get_type_display', read_only=True)  # 获取choice字段的可读名称

    # related_object_url = serializers.SerializerMethodField() # 可选: 生成关联对象URL的字段

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_info', 'sender', 'sender_info',
            'type', 'type_display',  # 使用 type_display 代替 get_type_display
            'title', 'content', 'timestamp', 'is_read', 'read_at',
            'content_type', 'object_id',  # 'related_object_url',
            'can_recipient_delete', 'can_recipient_reply',
            'parent_notification', 'data'
        ]
        read_only_fields = [
            'id', 'recipient_info', 'sender_info', 'type_display',
            'timestamp', 'read_at', 'content_type', 'object_id'
        ]
        # 确保 recipient 和 sender 在创建时是可写的，但通常通过 perform_create 设置
        extra_kwargs = {
            'recipient': {'write_only': True, 'required': False},  # 通常在视图中设置
            'sender': {'write_only': True, 'required': False},  # 通常在视图中设置
        }

    # def get_related_object_url(self, obj):
    #     if obj.related_object:
    #         # 这需要您有一个URL命名约定或注册表
    #         # 示例: 如果关联对象有 get_absolute_url 方法，则 return obj.related_object.get_absolute_url()
    #         return None # 替换为实际的URL生成逻辑
    #     return None

    def create(self, validated_data):
        # 设置 can_recipient_delete 和 can_recipient_reply 的逻辑
        # 也可以在信号或视图中完成此操作
        notification_type = validated_data.get('type')
        recipient = validated_data.get('recipient')  # recipient 对象
        sender = validated_data.get('sender')  # sender 对象
        recipient_role = recipient.role if recipient else None

        # 默认规则 (可在其他地方或通过信号被特定逻辑覆盖)
        if notification_type == 'private_message':
            validated_data['can_recipient_reply'] = True
            if recipient_role == 'student':
                # 学生不能删除来自教师/管理员的私信
                if sender and sender.role in ['teacher', 'admin', 'superadmin']:
                    validated_data['can_recipient_delete'] = False
                else:  # 来自其他学生的消息
                    validated_data['can_recipient_delete'] = True
            # 教师/管理员通常可以删除私信，除非来自超级管理员 (由策略处理)
        elif notification_type in ['assignment_new', 'assignment_graded', 'course_change', 'class_change',
                                   'system_announcement']:
            validated_data['can_recipient_delete'] = False  # 系统生成或重要信息
            validated_data['can_recipient_reply'] = False
        elif notification_type in ['forum_reply', 'forum_like_summary']:
            validated_data['can_recipient_delete'] = True  # 论坛相关通知用户可自行删除
            validated_data['can_recipient_reply'] = False  # 回复应在论坛内进行，而非通过通知系统

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
