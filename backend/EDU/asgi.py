import os
from django.core.asgi import get_asgi_application

# 1. 首先设置 Django 的 settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EDU.settings')

# 2. 调用 get_asgi_application() 来初始化 Django 的 app registry
#    这一步是关键，必须在导入我们自己的路由和消费者之前执行
django_asgi_app = get_asgi_application()

# 3. 在 Django 初始化完成后，再安全地导入 Channels 和我们的路由配置
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chatroom.routing

# 4. 定义协议路由器
application = ProtocolTypeRouter({
    # HTTP 请求走 Django 原有的 ASGI 应用
    "http": django_asgi_app,

    # WebSocket 请求走 Channels 的路由
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chatroom.routing.websocket_urlpatterns
        )
    ),
})
