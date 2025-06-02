# backend/course/urls.py  (建议替换整文件)

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    # 教师 / 管理员接口
    CourseViewSet, TeacherCourseClassViewSet, MaterialViewSet, HomeworkViewSet, available_courses,
    # 学生接口
    CourseListView, StudentCourseViewSet, StudentAssignmentViewSet,
    StudentFileUploadView, StudentDashboardView, AssignmentSubmissionView,
)

# ---------- 教师 / 管理员通用接口 ----------
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'teacher-course-classes', TeacherCourseClassViewSet, basename='teachercourseclass')
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'homeworks', HomeworkViewSet, basename='homework')

# ---------- 学生专用接口 ----------
student_router = DefaultRouter()
student_router.register(r'courses', StudentCourseViewSet, basename='student-course')
student_router.register(r'assignments', StudentAssignmentViewSet, basename='student-assignment')

urlpatterns = [
    # ========== 教师 / 管理员 ==========
    path('api/', include(router.urls)),
    path('api/available-courses/', available_courses, name='available-courses'),

    # ========== 学生 ==========
    path('student/', include(student_router.urls)),                              # 统一学生前缀

    path('student/assignments/overview/',
         StudentAssignmentViewSet.as_view({'get': 'overview'}),
         name='assignment-overview'),
    path('student/upload/', StudentFileUploadView.as_view(), name='student-file-upload'),
    path('student/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    
    # ======== 学生端·作业信息 / 我的提交 ========
    # 作业详情（Homework）    GET /cou/student/assignments/<assignment_id>/
    path(
        'student/assignments/<int:assignment_id>/',
        StudentAssignmentViewSet.as_view({'get': 'assignment_info'}),
        name='student-assignment-info'
    ),
    # 当前学生的提交          GET /cou/student/assignments/<assignment_id>/submissions/me/
    path(
        'student/assignments/<int:assignment_id>/submissions/me/',
        AssignmentSubmissionView.as_view({'get': 'retrieve_me'}),
        name='student-assignment-my-submission'
    ),
]

urlpatterns += [
    # 提交作业：POST /cou/student/assignments/<assignment_id>/submissions/
    path(
        'student/assignments/<int:assignment_id>/submissions/',
        AssignmentSubmissionView.as_view({'post': 'create'}),
        name='assignment-submission-create'
    ),
    # 撤回作业：DELETE /cou/student/assignments/submissions/<pk>/
    path(
        'student/assignments/submissions/<int:pk>/',
        AssignmentSubmissionView.as_view({'delete': 'destroy'}),
        name='assignment-submission-delete'
    ),
]