# backend/chatroom/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage, ChatRoomMember


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chatroom_{self.room_id}'
        self.user = self.scope['user']

        # 检查用户是否是该聊天室的成员
        if not self.user.is_authenticated or not await self.is_member():
            await self.close()
            return

        # 加入房间组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # (可选) 向群组广播用户上线消息
        # member = await self.get_member_instance()
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'system_message',
        #         'message': f'"{member.nickname}" 加入了聊天。'
        #     }
        # )

    async def disconnect(self, close_code):
        # 离开房间组
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 从 WebSocket 接收消息
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        # 根据消息类型调用不同的处理函数
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        # 未来可以扩展其他类型，如 typing, edit_message 等

    # --- 消息处理逻辑 ---

    async def handle_chat_message(self, data):
        message_content = data['message']
        member = await self.get_member_instance()

        if not member or not member.is_active:
            return  # 用户已被踢出

        # 检查是否全员禁言
        room = await database_sync_to_async(ChatRoom.objects.get)(id=self.room_id)
        if room.is_muted and member.role != 'admin':
            # (可选) 向发送者发送一个错误提示
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '当前聊天室已禁言。'
            }))
            return

        # 创建消息记录
        chat_message = await self.create_chat_message('text', message_content, member)

        # 广播消息到房间组
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',  # 这是下面要定义的处理函数名
                'message': {
                    'id': chat_message.id,
                    'author': {
                        'id': member.id,
                        'nickname': member.nickname,
                        'role': member.role,
                        'user_id': member.user.id
                    },
                    'message_type': 'text',
                    'content': chat_message.content,
                    'timestamp': chat_message.timestamp.isoformat()
                }
            }
        )

    # --- 广播处理函数 ---

    # 从房间组接收消息
    async def broadcast_message(self, event):
        # 将消息发送到 WebSocket
        await self.send(text_data=json.dumps(event['message']))

    async def system_message(self, event):
        # 广播系统消息
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': event['message'],
            'timestamp': event.get('timestamp')
        }))

    # --- 数据库交互辅助函数 ---

    @database_sync_to_async
    def is_member(self):
        return ChatRoomMember.objects.filter(room_id=self.room_id, user=self.user, is_active=True).exists()

    @database_sync_to_async
    def get_member_instance(self):
        try:
            return ChatRoomMember.objects.select_related('user').get(room_id=self.room_id, user=self.user)
        except ChatRoomMember.DoesNotExist:
            return None

    @database_sync_to_async
    def create_chat_message(self, msg_type, content, author):
        return ChatMessage.objects.create(
            room_id=self.room_id,
            author=author,
            message_type=msg_type,
            content=content
        )
