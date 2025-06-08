# backend/EDU/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chatroom.routing  # 导入我们即将创建的 chatroom 路由

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EDU.settings')

# get_asgi_application() 必须在 import 之后调用，以确保 Django App 已加载
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chatroom.routing.websocket_urlpatterns
        )
    ),
})
