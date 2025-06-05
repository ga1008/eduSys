"""
URL configuration for EDU project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('edu/', include('education.urls')),
    path('cou/', include('course.urls')),
    path('notifications/api/', include('notifications.urls')), # 新增此行
    # path('edu/api/courses/', include('course.urls_courses')),  # 添加课程API映射
    # path('edu/api/teacher-course-classes/', include('course.urls_tcc')),  # 添加班级绑定API映射

]

# 兜底：把剩下所有路径都返回 index.html
# urlpatterns += [
#     re_path(r"^.*/?$", TemplateView.as_view(template_name="index.html")),
# ]
