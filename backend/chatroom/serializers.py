# backend/chatroom/serializers.py

from rest_framework import serializers
from .models import ChatRoom, ChatRoomMember, ChatMessage
from utils.minio_tools import MinioClient


class ChatMessageSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    file_path = serializers.SerializerMethodField()
    thumbnail_path = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'author', 'message_type', 'content',
            'file_path', 'file_original_name', 'thumbnail_path',
            'timestamp'
        ]

    def get_author(self, obj):
        if obj.author:
            return {
                'id': obj.author.id,
                'nickname': obj.author.nickname,
                'role': obj.author.role,
                'user_id': obj.author.user_id,
            }
        return None

    def get_file_url(self, obj, field_name):
        """为给定字段从Minio获取预签名URL的辅助函数。"""
        object_name = getattr(obj, field_name, None)
        if object_name:
            if not hasattr(self, '_minio_client'):
                self._minio_client = MinioClient()
            return self._minio_client.get_file_url(object_name)
        return None

    def get_file_path(self, obj):
        """为主文件生成预签名URL。"""
        return self.get_file_url(obj, 'file_path')

    def get_thumbnail_path(self, obj):
        """为缩略图生成预签名URL。"""
        return self.get_file_url(obj, 'thumbnail_path')


class ChatRoomMemberSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoomMember
        fields = ['id', 'user', 'user_info', 'nickname', 'role', 'is_active']
        read_only_fields = ['user', 'user_info', 'is_active']

    def get_user_info(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'name': obj.user.name,
        }


class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'is_muted']
