from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ClassViewSet, StudentViewSet, login_view, logout_view, me_view, TeacherViewSet

router = DefaultRouter()
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'teachers', TeacherViewSet, basename='teacher')

urlpatterns = [
    path('api/login/', login_view, name='api_login'),
    path('api/logout/', logout_view, name='api_logout'),
    path('api/', include(router.urls)),
    # 移除冗余的导入路由，使用 ClassViewSet 的 action
    path('api/me/', me_view, name='api_me'),
    path('api/students/download_template/', StudentViewSet.as_view({'get': 'download_template'}),
         name='download-template'),
]
