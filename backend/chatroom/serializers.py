# backend/chatroom/serializers.py

from rest_framework import serializers
from .models import ChatRoom, ChatRoomMember, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

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
