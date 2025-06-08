# backend/chatroom/apps.py

from django.apps import AppConfig


class ChatroomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatroom'

    def ready(self):
        import chatroom.signals  # 导入 signals.py 以注册信号处理器
