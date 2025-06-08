# backend/chatroom/urls.py

from django.urls import path, include
from rest_framework_nested import routers
from .views import ChatRoomViewSet, ChatRoomAdminViewSet, ChatRoomMemberSelfViewSet

router = routers.DefaultRouter()
router.register(r'chatrooms', ChatRoomViewSet, basename='chatroom')

# 用于管理员操作的独立路由
admin_router = routers.DefaultRouter()
admin_router.register(r'chatrooms-admin', ChatRoomAdminViewSet, basename='chatroom-admin')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(admin_router.urls)),
    # 单独为成员自身操作创建的路由
    path('chatrooms/<int:pk>/me/', ChatRoomMemberSelfViewSet.as_view({'patch': 'partial_update'}), name='chatroom-me'),
]
