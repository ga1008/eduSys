# backend/course/views.py
import logging
import os
from io import BytesIO

import httpx
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import generics, status, permissions, viewsets
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from education.models import User, Material, Class
from utils.minio_tools import MinioClient
from .models import Assignment
from .models import Course, TeacherCourseClass, AssignmentSubmission, AssignmentSubmissionFile
from .permissions import IsTeacher, IsTeacherOrAdmin, IsStudent
from .serializers import CourseInfoSerializer, AssignmentSubmissionSerializer, \
    StudentDashboardSerializer, StudentCourseCardSerializer, StudentCourseDetailSerializer
from .serializers import CourseSerializer, CourseBriefSerializer, TeacherCourseClassSerializer, MaterialSerializer, \
    HomeworkSerializer
from .utils import ALLOWED_EXTENSIONS, read_uploaded_file_content, MAX_CONTENT_LENGTH, extract_json_from_string

logger = logging.getLogger(__name__)


@action(detail=True, methods=['get'])
def classes(self, request, pk=None):
    course = self.get_object()
    bindings = TeacherCourseClass.objects.filter(course=course)
    serializer = TeacherCourseClassSerializer(bindings, many=True)
    return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    # 基础权限：登录用户均可进入，但在具体操作中细分（也可用自定义组合权限类）
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # 超级管理员可以查看所有课程
        if user and getattr(user, 'is_superuser', False):
            return Course.objects.all()
        # 学生只能查看自己班级的课程
        if user and getattr(user, 'role', None) == 'Student':
            if hasattr(user, 'class_obj'):
                return Course.objects.filter(teachercourseclass__class_obj=user.class_obj).distinct()
            else:
                return Course.objects.none()
        if self.request.user.role == 'teacher':
            # 获取教师教授的课程ID
            course_ids = TeacherCourseClass.objects.filter(
                teacher=self.request.user
            ).values_list('course_id', flat=True)
            qs = Course.objects.filter(id__in=course_ids)
        else:
            qs = Course.objects.none()

            # 搜索功能
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return qs

    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """获取指定课程绑定的班级列表"""
        course = self.get_object()

        # 获取课程关联的班级绑定记录
        bindings = TeacherCourseClass.objects.filter(course=course)

        # 处理搜索
        search = request.query_params.get('search', '')
        if search:
            bindings = bindings.filter(
                Q(class_obj__name__icontains=search) |
                Q(teacher__name__icontains=search)
            )

        # 处理分页
        page = self.paginate_queryset(bindings)
        if page is not None:
            serializer = TeacherCourseClassSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TeacherCourseClassSerializer(bindings, many=True)
        return Response(serializer.data)

    def get_serializer_class(self):
        user = self.request.user
        # 学生使用精简序列化器，超级管理员使用完整序列化器
        if user and getattr(user, 'role', None) == 'Student':
            return CourseBriefSerializer
        return CourseSerializer

    def create(self, request, *args, **kwargs):
        # 仅超级管理员可以创建课程
        if not request.user or not getattr(request.user, 'is_superuser', False):
            return Response({"detail": "无权限创建课程"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 仅超级管理员可以更新课程
        if not request.user or not getattr(request.user, 'is_superuser', False):
            return Response({"detail": "无权限修改课程"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 仅超级管理员可以删除课程
        if not request.user or not getattr(request.user, 'is_superuser', False):
            return Response({"detail": "无权限删除课程"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def studentscount(self, request, pk=None):
        """获取该教学班的学生总数，post数据：{"classID": 1}"""
        course = self.get_object()
        class_id = request.data.get('classID')
        if not class_id:
            return Response({"detail": "必须提供班级ID"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取该课程下的班级
        try:
            teaching_class = TeacherCourseClass.objects.get(course=course, class_obj__id=class_id)
            students_count = User.objects.filter(
                class_enrolled=teaching_class.class_obj,
                role='student'
            ).count()
            return Response({"students_count": students_count})
        except TeacherCourseClass.DoesNotExist:
            return Response({"detail": "班级不存在或未绑定此课程"}, status=status.HTTP_404_NOT_FOUND)


class TeacherCourseClassViewSet(viewsets.ModelViewSet):
    queryset = TeacherCourseClass.objects.all()
    serializer_class = TeacherCourseClassSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # 获取对象
        obj = super().get_object()
        # 权限检查 - 教师只能访问自己的教学班级
        user = self.request.user
        if user.role == 'teacher' and obj.teacher != user:
            raise PermissionDenied("您无权访问此教学班级")
        return obj

    def get_queryset(self):
        user = self.request.user
        if user and getattr(user, 'is_superuser', False):
            # 超级管理员可以查看所有记录，支持通过查询参数过滤
            queryset = TeacherCourseClass.objects.all()
            course_id = self.request.query_params.get('course')
            class_id = self.request.query_params.get('class')
            teacher_id = self.request.query_params.get('teacher')
            if course_id:
                queryset = queryset.filter(course__id=course_id)
            if class_id:
                queryset = queryset.filter(class_obj__id=class_id)
            if teacher_id:
                queryset = queryset.filter(teacher__id=teacher_id)
            return queryset
        if user and getattr(user, 'role', None) == 'teacher':
            # 教师只查看自己的教学单元
            qs = TeacherCourseClass.objects.filter(teacher=self.request.user)
            # 支持按课程、班级过滤
            course_id = self.request.query_params.get('course_id')
            class_id = self.request.query_params.get('class_id')

            if course_id:
                qs = qs.filter(course_id=course_id)
            if class_id:
                qs = qs.filter(class_obj_id=class_id)

            # 搜索功能
            search = self.request.query_params.get('search', '')
            if search:
                qs = qs.filter(
                    Q(course__name__icontains=search) |
                    Q(class_obj__name__icontains=search) |
                    Q(textbook__icontains=search)
                )

            return qs
        if user and getattr(user, 'role', None) == 'student':
            # 学生不开放此接口，也可选择返回本班级记录但不包含内部字段
            return TeacherCourseClass.objects.none()
        return TeacherCourseClass.objects.none()

    def create(self, request, *args, **kwargs):
        # 仅超级管理员可创建教学单元
        if not request.user or not getattr(request.user, 'is_superuser', False):
            return Response({"detail": "无权限创建教学单元"}, status=status.HTTP_403_FORBIDDEN)
        # 检查是否重复绑定
        course = request.data.get('course')
        class_obj = request.data.get('class_obj')
        if TeacherCourseClass.objects.filter(course_id=course, class_obj_id=class_obj).exists():
            return Response({"detail": "该课程已绑定该班级，不能重复创建"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 获取待修改对象
        instance = self.get_object()
        user = request.user
        # 如果是教师，只允许修改教材/大纲/进度
        if user and getattr(user, 'role', None) == 'Teacher':
            # 移除教师不允许修改的字段
            disallowed_fields = ('course', 'class_obj', 'teacher')
            for field in disallowed_fields:
                request.data.pop(field, None)
            # 确保教师只能修改自己的记录
            if instance.teacher_id != user.id:
                return Response({"detail": "无权限修改该教学单元"}, status=status.HTTP_403_FORBIDDEN)
        # 超级管理员可以修改任意字段（包括调整teacher或更新信息）
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 仅超级管理员可删除
        if not request.user or not getattr(request.user, 'is_superuser', False):
            return Response({"detail": "无权限删除教学单元"}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsTeacher])
    def upload_resource(self, request, pk=None):
        """
        资源上传接口（预留）。
        教师可以通过此接口上传课件等资源到教学单元。
        当前为占位实现。
        """
        return Response({"detail": "资源上传功能尚未实现"}, status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """获取课程教学进度（占位功能，后续实现）"""
        teaching_class = self.get_object()
        # 这里只返回简单数据，实际实现会更复杂
        return Response({
            "course": teaching_class.course.name,
            "class": teaching_class.class_obj.name,
            "progress": teaching_class.progress or "暂无进度信息",
            "completion_rate": 0,  # 将来计算班级作业完成率
        })

    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """更新课程教学进度"""
        teaching_class = self.get_object()
        progress = request.data.get('progress')

        if progress is not None:
            teaching_class.progress = progress
            teaching_class.save(update_fields=['progress'])
            return Response({"detail": "教学进度已更新"})
        else:
            return Response({"detail": "未提供进度信息"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """获取该教学班的所有学生"""
        teaching_class = self.get_object()
        students = User.objects.filter(
            class_enrolled=teaching_class.class_obj,
            role='student'
        )

        # 支持搜索
        search = request.query_params.get('search', '')
        if search:
            students = students.filter(
                Q(name__icontains=search) |
                Q(student_number__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(qq__icontains=search)
            )

        from education.serializers import StudentSerializer
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def students_count(self, request, pk=None):
        """获取该教学班的学生总数"""
        teaching_class = self.get_object()
        students_count = User.objects.filter(
            class_enrolled=teaching_class.class_obj,
            role='student'
        ).count()
        return Response({"students_count": students_count})

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """教师仪表板数据"""
        # 获取当前教师的信息
        teacher = request.user
        # 获取该教师教授的所有课程班级
        courses = TeacherCourseClass.objects.filter(teacher=teacher)

        # 统计数据
        course_count = courses.count()
        # 获取学生数量（所有教授班级中的学生总数）
        classes = set()
        students = set()
        for tcc in courses:
            tcc_c_id = tcc.class_obj.id
            if tcc_c_id not in classes:
                classes.add(tcc.class_obj.id)
                # 获取该班级学生数
                students |= set(User.objects.filter(
                    class_enrolled=tcc.class_obj,
                    role='student'
                ).values_list("student_number"))

        # 最近的课程（按开始日期排序）
        recent_courses = TeacherCourseClassSerializer(
            courses.order_by('-start_date'),
            many=True
        ).data

        return Response({
            'teacher': {
                'name': teacher.name or teacher.username,
                'teacher_number': teacher.teacher_number,
                'email': teacher.email
            },
            'stats': {
                'course_count': course_count,
                'class_count': len(classes),
                'student_count': len(students)
            },
            'recent_courses': recent_courses
        })

    @action(detail=False, methods=['get'])
    def courses(self, request):
        """获取教师教授的所有课程"""
        user = self.request.user
        if user and getattr(user, 'role', None) == 'teacher':
            # 使用 select_related 预加载关联对象，减少数据库查询次数
            courses = TeacherCourseClass.objects.filter(teacher=user).select_related(
                'course', 'class_obj', 'teacher'
            )
            # 添加缓存控制
            serializer = TeacherCourseClassSerializer(courses, many=True)
            return Response(serializer.data)
        return Response({"detail": "无权限访问"}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['get'], url_path=r'students/(?P<student_id>\d+)')
    def student_detail(self, request, pk=None, student_id=None):
        """获取教学班级中单个学生的详细信息"""
        try:
            # 获取当前课程班级
            course_class = self.get_object()

            # 检查权限：只有该课程的教师或管理员可查看
            if course_class.teacher != request.user and not request.user.is_superuser:
                return Response({"detail": "无权查看此学生详情"}, status=status.HTTP_403_FORBIDDEN)

            # 获取学生信息
            student = User.objects.get(pk=student_id)

            # 检查学生是否属于该班级
            if student.class_enrolled != course_class.class_obj:
                return Response({"detail": "该学生不属于此班级"}, status=status.HTTP_400_BAD_REQUEST)

            # 获取最后一次提交作业信息
            last_submission = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course_class=course_class
            ).order_by('-submit_time').first()

            # 作业提交统计
            submissions_stats = AssignmentSubmission.objects.filter(
                student=student,
                assignment__course_class=course_class
            ).aggregate(
                total=Count('id'),
                graded=Count('id', filter=Q(score__isnull=False)),
                avg_score=Avg('score', filter=Q(score__isnull=False))
            )

            # 构建响应数据
            data = {
                "student": {
                    "id": student.id,
                    "name": student.name,
                    "student_number": student.student_number,
                    "email": student.email,
                    "last_login": student.last_login,
                },
                "education": {
                    "class_name": student.class_enrolled.name,
                    "major": getattr(student.class_enrolled, 'major', '未设置'),
                    "department": getattr(student.class_enrolled, 'department', '未设置'),
                    "grade": getattr(student.class_enrolled, 'year', '未知'),
                },
                "activities": {
                    "submissions_stats": submissions_stats,
                    "last_submission": None
                }
            }

            # 添加最后提交信息
            if last_submission:
                data["activities"]["last_submission"] = {
                    "assignment_title": last_submission.assignment.title,
                    "submit_time": last_submission.submit_time,
                    "score": last_submission.score,
                    "is_returned": last_submission.is_returned,
                }

            return Response(data)

        except User.DoesNotExist:
            return Response({"detail": "学生不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"获取学生详情失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_courses(request):
    """获取教师可以导入的课程列表（未绑定的课程班级）"""
    # 获取查询参数
    search = request.query_params.get('search', '')
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))

    # 查询当前教师已经绑定的课程班级 - 这里修改字段名
    existing = TeacherCourseClass.objects.filter(teacher=request.user).values_list(
        'course_id', 'class_obj_id')  # 修改 class_group_id 为 class_obj_id
    existing_pairs = set((c, cl) for c, cl in existing)

    # 查询所有课程
    courses = Course.objects.all()
    if search:
        courses = courses.filter(name__icontains=search)

    # 查询所有班级
    classes = Class.objects.all()
    if search:
        classes = classes.filter(Q(name__icontains=search))

    # 生成课程班级组合，排除已绑定的
    results = []
    for course in courses:
        for class_obj in classes:
            if (course.id, class_obj.id) not in existing_pairs:
                results.append({
                    'course_id': course.id,
                    'course_name': course.name,
                    'course_code': course.code,
                    'class_id': class_obj.id,
                    'class_name': class_obj.name,
                    'credit': course.credit
                })

    # 分页
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_results = results[start:end]

    return Response({
        'count': total,
        'results': paginated_results
    })


class MaterialViewSet(viewsets.ModelViewSet):
    """教学资源管理视图集"""
    serializer_class = MaterialSerializer
    permission_classes = [IsTeacherOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # 管理员可以查看所有资源，教师只能查看自己的资源
        if self.request.user.role in ['admin', 'superadmin']:
            qs = Material.objects.all()
        else:
            # 获取教师关联的教学班级ID
            teaching_classes = TeacherCourseClass.objects.filter(
                teacher=self.request.user
            ).values_list('id', flat=True)

            qs = Material.objects.filter(teaching_class_id__in=teaching_classes)

        # 支持按教学班级过滤
        teaching_class_id = self.request.query_params.get('teaching_class_id')
        if teaching_class_id:
            qs = qs.filter(teaching_class_id=teaching_class_id)

        # 支持按资料类型过滤
        material_type = self.request.query_params.get('type')
        if material_type:
            qs = qs.filter(material_type=material_type)

        # 搜索功能
        search = self.request.query_params.get('search', '')
        if search:
            qs = qs.filter(title__icontains=search)

        return qs

    def perform_create(self, serializer):
        # 设置上传者为当前用户
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='batch-upload')
    def batch_upload(self, request):
        """批量上传教学资源"""
        teaching_class_id = request.data.get('teaching_class_id')
        if not teaching_class_id:
            return Response({"detail": "必须指定教学班级ID"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            teaching_class = TeacherCourseClass.objects.get(id=teaching_class_id)

            # 权限检查
            if teaching_class.teacher != request.user and request.user.role not in ['admin', 'superadmin']:
                return Response({"detail": "无权限操作此教学班级"}, status=status.HTTP_403_FORBIDDEN)

            # 获取上传的文件
            files = request.FILES.getlist('files')
            if not files:
                return Response({"detail": "未提供文件"}, status=status.HTTP_400_BAD_REQUEST)

            # 批量创建资源
            created_materials = []
            for file in files:
                material = Material(
                    title=file.name,
                    file=file,
                    uploaded_by=request.user,
                    teaching_class=teaching_class
                )
                material.save()
                created_materials.append(material)

            serializer = MaterialSerializer(created_materials, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except TeacherCourseClass.DoesNotExist:
            return Response({"detail": "教学班级不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": f"上传失败: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HomeworkViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = HomeworkSerializer  # 需要定义序列化器
    permission_classes = [IsTeacherOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user and getattr(user, 'is_superuser', False):
            return Assignment.objects.all()

        # 如果有参数course_class=id，则只返回该课程班级的作业
        course_class_id = self.request.query_params.get('course_class')
        qs = Assignment.objects.filter(course_class_id=course_class_id) if course_class_id else Assignment.objects.all()
        if user and getattr(user, 'role', None) == 'teacher':
            return qs.filter(course_class__teacher=user)
        if user and getattr(user, 'role', None) == 'student':
            return qs.filter(course_class__class_obj__students=user)
        return Assignment.objects.none()

    def perform_create(self, serializer):
        # 设置发布人
        serializer.save(deployer=self.request.user)

    def perform_update(self, serializer):
        # 设置发布人
        serializer.save(deployer=self.request.user)

    @action(detail=True, methods=['patch'], url_path='toggle-ai-grading')
    def toggle_ai_grading(self, request, pk=None):
        assignment = self.get_object()
        # 权限检查：确保是作业的部署者或相关教师
        if assignment.deployer != request.user and assignment.course_class.teacher != request.user:
            if not request.user.role in ['admin', 'superadmin']:  # 管理员豁免
                return Response({"detail": "无权限修改此作业的AI批改设置"}, status=status.HTTP_403_FORBIDDEN)

        enabled_flag = request.data.get('ai_grading_enabled')
        if enabled_flag is None or not isinstance(enabled_flag, bool):
            return Response({"detail": "请提供 'ai_grading_enabled' (布尔值)"}, status=status.HTTP_400_BAD_REQUEST)

        assignment.ai_grading_enabled = enabled_flag
        assignment.save(update_fields=['ai_grading_enabled'])

        # 如果开启AI批改但没有提示词，可以考虑设置一个默认提示词或警告
        # if assignment.ai_grading_enabled and not assignment.ai_grading_prompt:
        #     # 这里可以生成一个默认的 prompt，但通常前端处理更好
        #     # assignment.ai_grading_prompt = f"课程《{assignment.course_class.course.name}》的作业《{assignment.title}》..."
        #     # assignment.save(update_fields=['ai_grading_prompt'])
        #     logger.warning(f"AI grading enabled for assignment {assignment.id} without a prompt.")

        return Response(
            {"detail": f"AI辅助批改已{'启用' if assignment.ai_grading_enabled else '禁用'}",
             "ai_grading_enabled": assignment.ai_grading_enabled},
            status=status.HTTP_200_OK
        )

    # 支持删除操作
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.deployer != request.user and request.user.role != 'admin':
            return Response({"detail": "无权限删除此作业"}, status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ---------- 老师查看学生提交的未批改的作业 ----------
    @action(detail=False, methods=['get'], url_path='ungraded')
    def ungraded_submissions(self, request):
        """
        GET /cou/api/homeworks/ungraded/
        返回当前学生未批改的作业提交列表
        """
        student = request.user
        # 获取当前学生的所有未批改作业提交
        submissions = AssignmentSubmission.objects.filter(
            student=student, score__isnull=True, is_returned=False
        ).select_related('student')

        data = []
        for sub in submissions:
            temp = {
                'id': sub.id,
                'title': sub.title,
                'content': sub.content,
                'submit_time': sub.submit_time,
                'student_id': sub.student.id,
                'student_name': sub.student.name,
                'student_number': sub.student.student_number,
                'class_name': sub.student.class_enrolled.name,
            }
            data.append(temp)
        return Response(data)

    # --------- 学生提交列表 ----------
    @action(detail=True, methods=['get'], permission_classes=[IsTeacherOrAdmin])
    def submissions(self, request, pk=None):
        """
        GET /cou/api/homeworks/<id>/submissions/?only_ungraded=true
        """
        hw = self.get_object()
        qs = AssignmentSubmission.objects.filter(assignment=hw).select_related('student')
        if request.query_params.get('only_ungraded') == 'true':
            qs = qs.filter(score__isnull=True, submitted=True)

        minio_client = MinioClient()
        data = []
        # 携带学生姓名、id、学号、班级名称、班级id
        for sub in qs:
            student = sub.student
            temp = {
                'id': sub.id,
                'student_id': student.id,
                'student_name': student.name,
                'student_number': student.student_number,
                'class_name': student.class_enrolled.name,
                'class_id': student.class_enrolled.id,
                'course_name': sub.assignment.course_class.course.name,
                'course_id': sub.assignment.course_class.course.id,
                'submit_time': sub.submit_time,
                'score': sub.score,
                'teacher_comment': sub.teacher_comment,
                'is_returned': sub.is_returned,
                'title': sub.title,
                'content': sub.content,
                'assignment': sub.assignment.id,
            }
            file_list = []
            for file in AssignmentSubmissionFile.objects.filter(submission=sub):
                file_list.append({
                    'id': file.id,
                    'file_name': file.file_name,
                    'original_name': file.original_name,
                    'update_time': file.update_time,
                    'url': minio_client.get_file_url(object_name=file.file_name),
                })
            temp.update({'files': file_list})
            data.append(temp)
        return Response(data)

    # ---------- 查看某个学生提交的作业 ----------
    @action(detail=False, methods=['get'], url_path=r'submissions/(?P<pk>\d+)',
            permission_classes=[IsTeacherOrAdmin])
    def submission_detail(self, request, pk=None):
        """
        GET /cou/api/homeworks/submissions/<pk>/
        返回指定提交的详细信息，包括附件下载链接
        """
        try:
            sub = AssignmentSubmission.objects.get(pk=pk)
        except AssignmentSubmission.DoesNotExist:
            return Response({"detail": "提交不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 权限：必须是该作业的任课教师或提交者
        if sub.assignment.course_class.teacher != request.user and sub.student != request.user:
            return Response({"detail": "无权查看此提交"}, status=403)
        student = sub.student
        minio_client = MinioClient()
        data = AssignmentSubmissionSerializer(sub, context={'request': request}).data
        data['files'] = []
        for file in AssignmentSubmissionFile.objects.filter(submission=sub):
            data['files'].append({
                'id': file.id,
                'file_name': file.file_name,
                'original_name': file.original_name,
                'update_time': file.update_time,
                'url': minio_client.get_file_url(object_name=file.file_name),
            })
        data['student'] = {
            'id': student.id,
            'name': student.name,
            'student_number': student.student_number,
            'class_name': student.class_enrolled.name,
            'class_id': student.class_enrolled.id,
        }
        return Response(data)

    # --------- 批改 / 退回 ----------
    @action(detail=False, methods=['patch'], url_path=r'submissions/(?P<pk>\d+)/grade',
            permission_classes=[IsTeacherOrAdmin])
    def grade(self, request, pk=None):
        """
        PATCH /cou/api/homeworks/submissions/<pk>/grade/
        body: { "score": 95, "teacher_comment": "Good", "is_returned": false }
        """
        sub = AssignmentSubmission.objects.get(pk=pk)
        hw = sub.assignment
        # 权限：必须是该作业的任课教师
        if hw.course_class.teacher != request.user:
            return Response({"detail": "无权批改此提交"}, status=403)

        score = request.data.get('score')
        comment = request.data.get('teacher_comment', '')
        returned = request.data.get('is_returned', False)

        sub.score = score if score is not None else sub.score
        if returned:
            sub.score = None
            sub.submitted = False

        sub.teacher_comment = comment
        sub.is_returned = returned
        sub.save(update_fields=['score', 'teacher_comment', 'is_returned', 'update_time'])

        return Response(AssignmentSubmissionSerializer(sub, context={'request': request}).data)


# 新增在学生端课程视图
class StudentCourseViewSet(viewsets.ReadOnlyModelViewSet):
    """学生课程信息视图（只读）"""
    # serializer_class = StudentCourseCardSerializer # 列表视图将使用这个
    permission_classes = [IsStudent]  #

    def get_queryset(self):
        student = self.request.user
        # 确保 student 对象存在并且有关联的班级
        if not student or not hasattr(student, 'class_enrolled') or not student.class_enrolled:
            return TeacherCourseClass.objects.none()  # 如果没有班级信息，返回空查询集

        return TeacherCourseClass.objects.filter(
            class_obj=student.class_enrolled
        ).select_related('course', 'teacher')

    def get_serializer_class(self):
        if self.action == 'retrieve':  # 当获取单个课程详情时
            return StudentCourseDetailSerializer  # 使用新的详细序列化器
        return StudentCourseCardSerializer  # 列表视图使用简要序列化器

    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        """获取课程关联的教学资源"""
        tcc = self.get_object()  # pk 是 TeacherCourseClass 的 ID
        materials = Material.objects.filter(
            teaching_class=tcc  # material 模型中的 teaching_class 字段关联 TeacherCourseClass
        ).order_by('-upload_time')

        search = request.query_params.get('search')
        material_type = request.query_params.get('type')
        if search:
            materials = materials.filter(title__icontains=search)
        if material_type:
            materials = materials.filter(material_type=material_type)

        page = self.paginate_queryset(materials)
        # 注意：这里应该使用 MaterialSerializer，确保它已在 serializers.py 中定义或导入
        from .serializers import MaterialSerializer  # 确保引入 MaterialSerializer
        serializer = MaterialSerializer(page if page is not None else materials, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """获取课程关联的作业列表"""
        tcc = self.get_object()  # pk 是 TeacherCourseClass 的 ID
        # 假设 Assignment 模型有一个 active 字段来控制作业是否对学生可见
        assignments_qs = Assignment.objects.filter(
            course_class=tcc, active=True
        ).order_by('-due_date')

        search = request.query_params.get('search')
        if search:
            assignments_qs = assignments_qs.filter(title__icontains=search)

        # 获取学生对这些作业的提交情况
        student_submissions = AssignmentSubmission.objects.filter(
            student=request.user,
            assignment__in=assignments_qs
        ).values(
            'assignment_id', 'score', 'submitted', 'is_returned', 'submit_time',
            'ai_comment', 'ai_score', 'ai_generated_similarity', 'ai_grading_status', 'ai_grading_task_id'
        )  #

        submissions_map = {sub['assignment_id']: sub for sub in student_submissions}

        # 序列化作业列表，并附带提交状态
        # 这里可以使用一个专门的序列化器，或者在视图中手动构建数据
        # 为简化，此处手动构建
        result_data = []
        for assignment in assignments_qs:
            submission_info = submissions_map.get(assignment.id)
            data = {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'due_date': assignment.due_date,
                'max_score': assignment.max_score,  #
                'deploy_date': assignment.deploy_date,
                # 课程和教师信息可以从 tcc 获取，避免重复查询
                'course_name': tcc.course.name,
                'teacher_name': tcc.teacher.name or tcc.teacher.username,
                'submitted': False,
                'score': None,
                'is_returned': False,
                'submit_time': None
            }
            if submission_info:
                data.update({
                    'submitted': submission_info['submitted'],
                    'score': submission_info['score'],
                    'is_returned': submission_info['is_returned'],
                    'submit_time': submission_info['submit_time'],
                    'ai_comment': submission_info.get('ai_comment', None),  # AI批改评论
                    'ai_score': submission_info.get('ai_score', None),  # AI批改分数
                    'ai_generated_similarity': submission_info.get('ai_generated_similarity', 0),  # AI生成的相似度
                    'ai_grading_status': submission_info.get('ai_grading_status', 'pending'),  # AI批改状态
                    'ai_grading_task_id': submission_info.get('ai_grading_task_id', None),  # AI批改任务ID
                })
            result_data.append(data)

        page = self.paginate_queryset(result_data)  # 对结果列表进行分页
        if page is not None:
            return self.get_paginated_response(page)  # DRF 会自动处理列表的分页响应
        return Response(result_data)


class StudentAssignmentViewSet(viewsets.ModelViewSet):
    """学生作业管理视图集"""
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return AssignmentSubmission.objects.filter(
            student=self.request.user
        ).select_related('assignment__course_class')

    # ----------  新增：返回作业（Homework）详情 ----------
    @action(detail=False, methods=['get'], url_path=r'(?P<assignment_id>\d+)/assignment_info')
    def assignment_info(self, request, assignment_id=None):
        """
          GET /student/assignments/<assignment_id>/   →  作业详情
           只要同班学生即可查看

           {
                "id": 7,
                "title": "软工2301班python程序设计作业1",
                "description": "哈哈哈哈哈哈哈哈哈，哦哈哈哈哈哈",
                "due_date": "2025-04-19T18:00:00+08:00",
                "max_score": "100.00",
                "deploy_date": "2025-04-13T21:32:34.025923+08:00",
                "deployer": "2024010932",
                "active": true,
                "course_class": 5,
                "course_class_name": "python程序设计"
            }
        """
        try:
            hw = Assignment.objects.get(pk=assignment_id)
        except Assignment.DoesNotExist:
            return Response({"detail": "作业不存在"}, status=status.HTTP_404_NOT_FOUND)

        if not hw.active:
            return Response({"detail": "作业已关闭"}, status=status.HTTP_400_BAD_REQUEST)

        # 权限：必须是同一个班级
        if hw.course_class.class_obj != getattr(request.user, "class_enrolled", None):
            return Response({"detail": "无权限访问该作业"}, status=status.HTTP_403_FORBIDDEN)

        hw_data = {
            "id": hw.id,
            "title": hw.title,
            "description": hw.description,
            "due_date": hw.due_date,
            "max_score": hw.max_score,
            "deploy_date": hw.deploy_date,
            "deployer": hw.deployer.teacher_number,
            "deployer_name": hw.deployer.name,
            "active": hw.active,
            "course_class": hw.course_class.id,
            "course_name": hw.course_class.course.name,
            "course_class_name": f"{hw.course_class.class_obj.name} - {hw.course_class.course.name}"
        }

        submissions = []
        submitted = False
        for ass in AssignmentSubmission.objects.filter(assignment_id=hw.id).order_by('-submit_time')[:5]:
            temp = {
                "submit_id": ass.id,
                "title": ass.title,
                "content": ass.content,
                "score": ass.score,
                "teacher_comment": ass.teacher_comment,
                "is_returned": ass.is_returned,
                "submit_time": ass.submit_time,
            }
            files = []
            for ass_f in AssignmentSubmissionFile.objects.filter(submission_id=ass.id):
                files.append({
                    'id': ass_f.id,
                    'file_name': ass_f.file_name,
                    'original_name': ass_f.original_name,
                    'update_time': ass_f.update_time
                })
            temp['files'] = files
            submissions.append(temp)

            if ass.submitted:
                submitted = True

        hw_data['last_submission'] = submissions[0] if submissions else {}
        hw_data['submissions'] = submissions
        hw_data['submitted'] = submitted
        return Response(hw_data)

    def update(self, request, *args, **kwargs):
        """
        PATCH /cou/student/assignments/submissions/<pk>/
        仅允许学生在【未过截止 && 未评分】状态下覆盖自己的提交；
        可在 body 中传递 delete_file_ids=[id1,id2] 删除旧附件，
        以及 files[]=<File> 重新上传新附件
        """
        submission = self.get_object()

        # 权限与时效校验
        if submission.student != request.user:
            return Response({"detail": "无权修改该提交"}, status=403)
        if submission.assignment.due_date < timezone.now():
            return Response({"detail": "已过截止时间，无法修改"}, status=400)
        if submission.score is not None:
            return Response({"detail": "已评分，无法修改"}, status=400)

        # 删除指定附件
        delete_ids = request.data.get('delete_file_ids', [])
        if delete_ids:
            AssignmentSubmissionFile.objects.filter(
                id__in=delete_ids, submission=submission
            ).delete()

        # 处理新增文件
        files = request.FILES.getlist('files')
        if files:
            minio_client = MinioClient()
            for f in files:
                buf = BytesIO(f.read())
                object_name = minio_client.upload_file(file_data=buf)
                AssignmentSubmissionFile.objects.create(
                    submission=submission,
                    file_name=object_name,
                    original_name=f.name
                )

        # 标题 / 内容
        submission.title = request.data.get('title', submission.title)
        submission.content = request.data.get('content', submission.content)
        submission.save()

        return Response(self.get_serializer(submission).data)

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """作业总览（按课程分组）"""
        submissions = self.get_queryset().values(
            'assignment__course_class__course__name',
            'assignment__course_class__id'
        ).annotate(
            total=Count('id'),
            submitted=Count('id', filter=Q(content__isnull=False)),
            graded=Count('id', filter=Q(score__isnull=False))
        )
        return Response(submissions)

    def create(self, request, *args, **kwargs):
        """提交作业（带文件上传校验）"""
        # 校验文件数量和大小
        files = request.FILES.getlist('files') or []
        if len(files) > 10:
            return Response({"detail": "最多上传10个文件"}, status=400)

        for file in files:
            if file.size > 10 * 1024 * 1024:  # 10MB限制
                return Response({"detail": f"文件 {file.name} 超过10MB限制"}, status=400)

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """撤回作业提交（需未过截止时间且未评分）"""
        if instance.assignment.due_date < timezone.now():
            raise ValidationError("已过截止时间，无法撤回提交")
        if instance.score is not None:
            raise ValidationError("作业已评分，无法撤回")
        super().perform_destroy(instance)


class CourseListView(generics.ListAPIView):
    """学生课程列表视图：列出学生所在班级的课程"""
    serializer_class = CourseInfoSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    def get_queryset(self):
        # 假设User有属性 student_class 指向学生所在班级
        student_class = getattr(self.request.user, "student_class", None)
        return TeacherCourseClass.objects.filter(clazz=student_class)


class AssignmentSubmissionView(viewsets.ModelViewSet):
    """
    作业提交视图集：
    提供 提交(create)、撤回删除(destroy) 功能。学生每次作业最多只能有一条提交记录。
    """
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    parser_classes = [MultiPartParser, FormParser]  # 允许解析multipart表单（用于文件上传）
    queryset = AssignmentSubmission.objects.all()  # 基础查询集（会在各动作中过滤）

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    def get_object(self):
        """获取当前用户的提交记录"""
        obj = super().get_object()
        if obj.student != self.request.user:
            raise PermissionDenied("无权访问该提交记录")
        return obj

    def get_queryset(self):
        # 学生只能查看/操作自己的提交
        return AssignmentSubmission.objects.filter(student=self.request.user)

    def create(self, request, *args, **kwargs):
        assignment_id = request.data.get('assignment')  # 前端发送的可能是 assignment ID
        if not assignment_id:  # 在您的urls.py中，assignment_id是从URL路径参数获取的
            assignment_id_from_url = kwargs.get('assignment_id')
            if not assignment_id_from_url:
                return Response({"detail": "必须提供作业ID (assignment ID)"}, status=status.HTTP_400_BAD_REQUEST)
            assignment_id = assignment_id_from_url

        try:
            assignment = Assignment.objects.get(pk=assignment_id)
        except Assignment.DoesNotExist:
            return Response({"detail": "指定的作业不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 权限与截止时间检查
        if assignment.course_class.class_obj != getattr(request.user, "class_enrolled", None):
            return Response({"detail": "无权限提交该作业"}, status=status.HTTP_403_FORBIDDEN)
        if timezone.now() > assignment.due_date:
            return Response({"detail": "已超过作业截止时间，不能提交"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查提交次数 (如果有限制)
        # existing_submissions_count = AssignmentSubmission.objects.filter(assignment=assignment, student=request.user).count()
        # if existing_submissions_count >= 5: # 假设最多提交5次
        #     return Response({"detail": "作业提交次数已达上限"}, status=status.HTTP_400_BAD_REQUEST)

        # 处理表单数据
        serializer_data = {
            "assignment": assignment.id,
            "title": request.data.get("title", f"{assignment.title} - 提交"),
            "content": request.data.get("content", ""),
            "submitted": True,
        }
        submission_serializer = self.get_serializer(data=serializer_data)
        submission_serializer.is_valid(raise_exception=True)
        submission = submission_serializer.save(student=request.user)  # 保存，确保 student 被设置

        # 处理文件上传
        uploaded_files_content = []
        uploaded_file_names = []
        files_to_process = request.FILES.getlist('files') or request.FILES.getlist('upload_files') or []

        can_ai_grade_files = True
        minio_client = MinioClient()

        for uploaded_file in files_to_process:
            original_name = uploaded_file.name
            file_ext = os.path.splitext(original_name)[1].lower()

            # MinIO上传逻辑保持不变
            try:
                file_data_bytes = uploaded_file.read()  # 读取文件数据以供上传
                uploaded_file.seek(0)  # 重置文件指针，以便后续可能的读取
                object_name_in_minio = minio_client.upload_file(file_data=file_data_bytes)
                AssignmentSubmissionFile.objects.create(
                    submission=submission,
                    file_name=object_name_in_minio,
                    original_name=original_name
                )
                uploaded_file_names.append(original_name)
            except Exception as e:
                logger.error(f"MinIO upload failed for {original_name}: {e}")
                # 可以选择是否因此中断整个提交过程
                submission.delete()  # 如果上传失败，回滚提交
                return Response({"detail": f"文件 {original_name} 上传失败: {e}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            if file_ext not in ALLOWED_EXTENSIONS:
                logger.info(
                    f"File {original_name} has unsupported extension {file_ext}, skipping AI grading for files.")
                can_ai_grade_files = False  # 一旦有不支持的文件，就不再尝试读取文件内容给AI
                # 不再读取这个文件，但其他允许的文件仍然可以尝试读取（如果策略如此）
                # 但当前策略是：只要有一个文件类型不支持，就不把任何文件内容给AI
                break  # 如果一个文件类型不合规，直接判定文件部分不适合AI

            if can_ai_grade_files:  # 只有在所有文件类型都符合的情况下才读取
                content = read_uploaded_file_content(uploaded_file)
                if content:
                    uploaded_files_content.append(f"\n\n--- 文件: {original_name} ---\n{content}")
                else:
                    logger.warning(f"Could not read content from allowed file: {original_name}")

        # --- AI 自动批改逻辑 ---
        if assignment.ai_grading_enabled:
            submission.ai_grading_status = 'pending'  # 先标记为待处理
            final_student_content = submission.content

            if not can_ai_grade_files:  # 如果文件类型不允许，则标记跳过
                logger.info(f"AI grading skipped for submission {submission.id} due to unsupported file types.")
                submission.ai_grading_status = 'skipped'
                submission.ai_comment = "由于提交了不支持AI分析的文件类型（如压缩包、图片等），本次未进行AI辅助批改。"
                submission.save(update_fields=['ai_grading_status', 'ai_comment'])
            else:
                for file_c in uploaded_files_content:
                    final_student_content += file_c

                if len(final_student_content) > MAX_CONTENT_LENGTH:
                    logger.info(
                        f"AI grading skipped for submission {submission.id} due to content length > {MAX_CONTENT_LENGTH}.")
                    submission.ai_grading_status = 'skipped'
                    submission.ai_comment = f"由于提交内容总字数超过{MAX_CONTENT_LENGTH}字，本次未进行AI辅助批改。"
                    submission.save(update_fields=['ai_grading_status', 'ai_comment'])
                else:
                    submission.ai_grading_status = 'processing'  # 标记为处理中
                    submission.save(update_fields=['ai_grading_status'])

                    ai_system_prompt = assignment.ai_grading_prompt or \
                                       f"课程《{assignment.course_class.course.name}》的作业《{assignment.title}》，描述：{assignment.description}。满分：{assignment.max_score}。请批改。"

                    user_content_for_ai = f"学生作业标题：{submission.title}\n学生提交内容：\n{final_student_content}"
                    if uploaded_file_names:  # 仅当有成功上传的文件时才添加这部分
                        user_content_for_ai += f"\n\n学生上传文件列表：{', '.join(uploaded_file_names)}"

                    messages_for_ai = [
                        {"role": "system", "content": ai_system_prompt},
                        {"role": "user", "content": user_content_for_ai}
                    ]

                    ai_request_payload = {
                        "messages": messages_for_ai,
                        "use_reasoning_model": True,  # 通常批改需要更好的模型
                        "model": None,  # 让AI服务自行选择
                        "provider": None,  # 让AI服务自行选择
                        "response_format": {"type": "json_object"}  # 明确要求JSON输出
                    }

                    logger.info(f"Sending request to AI service for submission {submission.id}")
                    try:
                        # 直接调用AI服务 (如果AI服务与Django在同一网络或可访问)
                        # 注意: 这里的AI_SERVICE_URL需要配置在Django settings或者.env
                        # from django.conf import settings
                        # ai_service_url = getattr(settings, 'AI_SERVICE_URL', 'http://localhost:8080/api/v1/chat/completions')
                        # 此处硬编码仅为示例，实际应从配置读取
                        ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:8080/api/v1/chat/completions')

                        # 使用 httpx 进行异步调用 (如果是在异步视图中) 或同步调用
                        # 当前视图是同步的，所以使用同步调用
                        # 对于可能耗时长的AI批改，最佳实践是通过Celery任务异步调用
                        # 这里简化为直接同步调用，并设置超时
                        # 后续应改为通过Celery任务调用AI服务的异步接口

                        task_payload = {
                            "request_data": ai_request_payload,  # AIRequest 字典
                            "submission_id": submission.id  # 传递 submission_id 以便回调更新
                        }
                        # 假设您的Celery任务名为 'ai_service.tasks.trigger_ai_grading_for_submission'
                        # from ai_service.celery_app import celery_app # 需要能访问到celery_app
                        # ai_task = celery_app.send_task('ai_service.tasks.trigger_ai_grading_for_submission', args=[task_payload])

                        # 暂时先不通过celery，直接调用 ai_service 的celery task分发接口
                        # 这个接口会返回 task_id
                        with httpx.Client(timeout=20.0) as client:  # 短超时，因为只是分发任务
                            response = client.post(ai_service_url, json=ai_request_payload)
                            response.raise_for_status()  # 如果HTTP状态码是4xx或5xx，则引发异常
                            ai_api_response = response.json()

                        if ai_api_response.get("success") and ai_api_response.get("task_id"):
                            submission.ai_grading_task_id = ai_api_response["task_id"]
                            submission.ai_grading_status = 'processing'  # 已发送给AI服务处理
                            logger.info(
                                f"AI grading task {submission.ai_grading_task_id} dispatched for submission {submission.id}.")
                        elif ai_api_response.get("success") and ai_api_response.get("content"):  # 如果AI服务同步返回了结果
                            logger.info(f"AI service returned synchronous result for submission {submission.id}")
                            raw_ai_output = ai_api_response.get("content")
                            parsed_json_result = extract_json_from_string(raw_ai_output)
                            if parsed_json_result and "score" in parsed_json_result and "comment" in parsed_json_result:
                                submission.ai_score = parsed_json_result.get("score")
                                # 确保分数不超过满分
                                if submission.ai_score is not None and assignment.max_score is not None:
                                    submission.ai_score = min(max(0, float(submission.ai_score)),
                                                              float(assignment.max_score))

                                submission.ai_comment = parsed_json_result.get("comment")
                                submission.ai_generated_similarity = parsed_json_result.get("AI生成疑似度")
                                submission.ai_grading_status = 'completed'
                                logger.info(
                                    f"AI grading completed for submission {submission.id}. Score: {submission.ai_score}")
                            else:
                                submission.ai_grading_status = 'failed'
                                submission.ai_comment = f"AI返回格式错误或缺少必要字段。原始输出: {raw_ai_output[:500]}"  # 只记录部分原始输出
                                logger.error(
                                    f"AI result parsing failed for submission {submission.id}. Raw: {raw_ai_output}")
                        else:  # AI API 调用失败或未返回 task_id
                            submission.ai_grading_status = 'failed'
                            submission.ai_comment = f"AI服务调用失败: {ai_api_response.get('error', '未知错误')}"
                            logger.error(
                                f"AI service call failed for submission {submission.id}: {ai_api_response.get('error')}")

                        submission.save()

                    except httpx.TimeoutException:
                        logger.error(f"AI service request timed out for submission {submission.id} (dispatching task).")
                        submission.ai_grading_status = 'failed'
                        submission.ai_comment = "AI服务请求超时（分发任务阶段）。"
                        submission.save(update_fields=['ai_grading_status', 'ai_comment'])
                    except httpx.RequestError as e:
                        logger.error(f"AI service request error for submission {submission.id}: {e}")
                        submission.ai_grading_status = 'failed'
                        submission.ai_comment = f"AI服务请求错误: {e}"
                        submission.save(update_fields=['ai_grading_status', 'ai_comment'])
                    except Exception as e:  # 其他未知错误
                        logger.error(f"Unexpected error during AI grading dispatch for submission {submission.id}: {e}",
                                     exc_info=True)
                        submission.ai_grading_status = 'failed'
                        submission.ai_comment = f"AI批改过程中发生未知错误: {e}"
                        submission.save(update_fields=['ai_grading_status', 'ai_comment'])
        else:  # AI批改未启用
            submission.ai_grading_status = 'skipped'
            submission.save(update_fields=['ai_grading_status'])

        # 返回创建的提交记录数据
        # 注意：此时的 submission 对象可能已经包含了 AI 批改的初步状态或 task_id
        # 但完整的AI结果是异步的，需要教师后续查看或系统轮询更新
        final_response_serializer = self.get_serializer(submission)
        return Response(final_response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """撤回作业提交（删除提交记录）"""
        submission = self.get_object()  # 确保只能删除自己的提交
        # 检查是否过了截止时间或已评分
        if timezone.now() > submission.assignment.due_date:
            return Response({"detail": "已过截止时间，无法撤回提交"}, status=status.HTTP_400_BAD_REQUEST)
        if submission.score is not None:
            return Response({"detail": "教师已批改评分，无法撤回提交"}, status=status.HTTP_400_BAD_REQUEST)
        # 删除提交记录和关联的附件记录（附件文件可选择是否从MinIO删除，这里假定不保留）
        # 可以调用 submission.files.all().delete() 级联删除 AssignmentSubmissionFile 记录
        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ----------  新增：获取当前学生的提交 ----------
    @action(detail=False, methods=['get'], url_path=r'(?P<assignment_id>\d+)/submissions/me')
    def retrieve_me(self, request, assignment_id=None):
        """
        GET /student/assignments/<assignment_id>/submissions/me/
        若无提交 → 404（前端据此判断“未提交”）
        """
        submission = AssignmentSubmission.objects.filter(
            assignment_id=assignment_id,
            student=request.user
        ).first()
        if not submission:
            return Response({"detail": "未找到提交记录"}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(submission).data)


class FileUploadView(generics.CreateAPIView):
    """通用文件上传接口（支持多文件），供教师和管理员使用"""
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('file') or request.FILES.getlist('files') or []
        if not files:
            return Response({"detail": "未收到文件"}, status=status.HTTP_400_BAD_REQUEST)
        # 初始化 MinIO 客户端
        minio_client = MinioClient()
        uploaded_files = []
        for file_obj in files:
            data = file_obj.read()
            object_name = minio_client.upload_file(file_data=data)
            uploaded_files.append({
                "name": file_obj.name,
                "url": minio_client.get_file_url(object_name=object_name)
            })
        # 返回上传成功的文件列表
        return Response({"files": uploaded_files}, status=status.HTTP_201_CREATED)


class StudentFileUploadView(FileUploadView):
    """学生专用文件上传（继承原有逻辑并增加限制）"""
    permission_classes = [IsStudent]

    def post(self, request, *args, **kwargs):
        # 限制总上传大小
        total_size = sum(f.size for f in request.FILES.getlist('files'))
        if total_size > 50 * 1024 * 1024:
            return Response({"detail": "总文件大小超过50MB限制"}, status=400)
        return super().post(request, *args, **kwargs)


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    # permission_classes = [AllowAny]
    def get(self, request):
        student = request.user
        serializer = StudentDashboardSerializer(student)
        return Response(serializer.data)
