# backend/chatroom/consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatRoomMember, ChatMessage
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from education.models import User
from django.conf import settings
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# 初始化一个异步的Redis连接
# 我们复用CHANNEL_LAYERS中的Redis配置
redis_client = redis.from_url(settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0])
USER_COUNT_KEY_PREFIX = "chatroom_user_count:"


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chatroom_{self.room_id}'

        # --- 用户身份验证 ---
        user = await self.get_user_from_scope()
        if user is None or user.is_anonymous:
            logger.warning(f"Chatroom {self.room_id}: Unauthenticated user tried to connect.")
            await self.close(code=4001)
            return
        self.scope['user'] = user

        # --- 检查用户是否为聊天室成员 ---
        self.member = await self.get_chatroom_member(user)
        if self.member is None:
            logger.warning(f"Chatroom {self.room_id}: User {user.username} is not a member, denying connection.")
            await self.close(code=4003)
            return

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Chatroom {self.room_id}: User {user.username} connected. Channel: {self.channel_name}")

        # --- 功能新增：更新并广播在线人数 ---
        await self.update_and_broadcast_user_count(1)

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # 离开房间组
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"Chatroom {self.room_id}: User {self.scope['user'].username} disconnected.")

            # --- 功能新增：更新并广播在线人数 ---
            await self.update_and_broadcast_user_count(-1)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'chat_message':
                message_content = data.get('message', '')
                if not message_content.strip():
                    return  # 忽略空消息

                # 保存消息到数据库
                message = await self.save_message(message_content)

                # 准备广播给所有人的消息体
                broadcast_data = await self.get_message_broadcast_data(message)

                # 广播消息
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_message',
                        'message': broadcast_data
                    }
                )
            else:
                logger.warning(f"Chatroom {self.room_id}: Received unknown message type '{message_type}'")

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from WebSocket message.")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    # --- Helper methods ---

    async def get_user_from_scope(self):
        """从scope中获取用户，支持JWT token"""
        if 'user' in self.scope and not isinstance(self.scope['user'], AnonymousUser):
            return self.scope['user']

        # 从查询字符串中解析token
        query_string = self.scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if not token:
            return AnonymousUser()

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = await self.get_user_by_id(user_id)
            return user
        except (TokenError, User.DoesNotExist):
            return AnonymousUser()

    # --- 功能新增：更新和广播人数的核心逻辑 ---
    async def update_and_broadcast_user_count(self, delta):
        """
        在Redis中更新在线用户数，并向聊天室广播新的人数。
        delta: 1 表示增加, -1 表示减少
        """
        redis_key = f"{USER_COUNT_KEY_PREFIX}{self.room_id}"

        # HINCRBY 是原子操作，线程安全
        new_count = await redis_client.incrby(redis_key, delta)

        # 确保计数不会变为负数
        if new_count < 0:
            new_count = 0
            await redis_client.set(redis_key, 0)

        # 向整个组广播更新后的人数
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_count_update',  # 新的事件类型
                'count': new_count
            }
        )

    # --- 事件处理器 ---

    async def broadcast_message(self, event):
        """从组接收到普通消息后，将其发送给WebSocket客户端"""
        await self.send(text_data=json.dumps(event['message']))

    async def user_count_update(self, event):
        """从组接收到人数更新事件后，将其发送给WebSocket客户端"""
        await self.send(text_data=json.dumps({
            'type': 'user_count_update',
            'count': event['count']
        }))

    # --- 数据库交互 ---

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_chatroom_member(self, user):
        try:
            return ChatRoomMember.objects.get(room_id=self.room_id, user=user, is_active=True)
        except ChatRoomMember.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, content):
        message = ChatMessage.objects.create(
            room_id=self.room_id,
            author=self.member,
            content=content,
            message_type='text'
        )
        return message

    @database_sync_to_async
    def get_message_broadcast_data(self, message):
        author_data = {
            'id': message.author.id,
            'nickname': message.author.nickname,
            'role': message.author.role,
            'user_id': message.author.user.id,
        }
        return {
            'id': message.id,
            'author': author_data,
            'message_type': message.message_type,
            'content': message.content,
            'file_path': None,
            'file_original_name': None,
            'thumbnail_path': None,
            'timestamp': message.timestamp.isoformat(),
        }
