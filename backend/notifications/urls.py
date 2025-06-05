# notifications/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationSettingsView, BlockedContactViewSet, UserSearchViewSet

router = DefaultRouter()
router.register(r'messages', NotificationViewSet, basename='notification')
router.register(r'blocked-contacts', BlockedContactViewSet, basename='blockedcontact')
router.register(r'search-users', UserSearchViewSet, basename='usersearch')  # 添加用户搜索路由

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', UserNotificationSettingsView.as_view(), name='notification-settings'),
]
