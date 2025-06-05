# backend/course/serializers.py
from django.db.models import Avg
from django.utils import timezone
from rest_framework import serializers

from education.models import Class, Material, User
from .models import Course, TeacherCourseClass, Assignment, AssignmentSubmission


class CourseSerializer(serializers.ModelSerializer):
    # classes 字段作为只读，显示绑定班级名称列表（选填）
    class_names = serializers.SerializerMethodField(read_only=True)

    def get_class_names(self, obj):
        # 返回该课程绑定的所有班级名称列表
        return [tc.class_obj.name for tc in obj.teachercourseclass_set.all()]

    class Meta:
        model = Course
        fields = ['id', 'name', 'credit', 'hours', 'description', 'class_names', 'code']
        read_only_fields = ['id', 'class_names']  # id 和 code 字段只读


class CourseBriefSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()

    def get_teacher_name(self, obj):
        """根据当前请求用户所属班级，从TeacherCourseClass获取教师姓名"""
        request = self.context.get('request')
        if request and hasattr(request.user, 'class_obj'):  # 假设User有属性指向所属班级对象
            tcc = TeacherCourseClass.objects.filter(course=obj, class_obj=request.user.class_obj).first()
            if tcc and tcc.teacher:
                return getattr(tcc.teacher, 'full_name', tcc.teacher.username)
        return None

    class Meta:
        model = Course
        fields = ['id', 'name', 'credit', 'hours', 'teacher_name']


class TeacherCourseClassSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    class_name = serializers.CharField(source='class_obj.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)

    # 计算学生人数
    students_count = serializers.SerializerMethodField()

    def get_students_count(self, obj):
        # 计算该班级的学生人数
        return obj.class_obj.students.count() if obj.class_obj else 0

    # 删除错误的source属性
    class_obj = serializers.PrimaryKeyRelatedField(
        queryset=Class.objects.all()
    )

    class Meta:
        model = TeacherCourseClass
        fields = ['id', 'course', 'course_name', 'class_obj', 'class_name', 'teacher', 'teacher_name',
                  'textbook', 'syllabus', 'progress', 'start_date', 'end_date', 'start_week', 'end_week',
                  'students_count']


class MaterialSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.name', read_only=True)
    course_name = serializers.CharField(source='teaching_class.course.name', read_only=True)
    class_name = serializers.CharField(source='teaching_class.class_obj.name', read_only=True)

    class Meta:
        model = Material
        fields = ['id', 'title', 'file', 'uploaded_by', 'uploaded_by_name',
                  'teaching_class', 'course_name', 'class_name', 'upload_time']
        read_only_fields = ['uploaded_by']


class HomeworkSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_empty_file=True)
    course_class_name = serializers.CharField(source='course_class.course.name', read_only=True)
    deployer = serializers.CharField(source='deployer.username', read_only=True)
    submit_count = serializers.SerializerMethodField()
    marked_count = serializers.SerializerMethodField()

    def get_submit_count(self, obj):
        """从子表 AssignmentSubmission 关联查询作业提交数量"""
        hid = obj.id
        return AssignmentSubmission.objects.filter(assignment_id=hid, submitted=True).count()

    def get_marked_count(self, obj):
        """从子表 AssignmentSubmission 关联查询已评分的作业数量"""
        hid = obj.id
        return AssignmentSubmission.objects.filter(assignment_id=hid, score__isnull=False, submitted=True).count()

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'max_score',
                  'deploy_date', 'deployer', 'active', 'file', 'course_class', 'course_class_name', 'submit_count',
                  'marked_count',
                  'ai_grading_enabled', 'ai_grading_prompt'
                  ]
        read_only_fields = ['deploy_date', 'deployer']


class AssignmentBriefSerializer(serializers.ModelSerializer):
    """作业简要信息"""
    status = serializers.SerializerMethodField()
    due_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    remaining_time = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course_class.course.name')

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'due_date', 'status', 'remaining_time', 'course_name']

    def get_status(self, obj):
        submission = obj.submissions.filter(student=self.context['request'].user).first()
        if not submission:
            return '未提交' if obj.due_date > timezone.now() else '已过期'
        if submission.score is not None:
            return f'已评分 ({submission.score})'
        return '已提交'

    def get_remaining_time(self, obj):
        delta = obj.due_date - timezone.now()
        if delta.days < 0:
            return "已过期"
        return f"{delta.days}天{delta.seconds // 3600}小时"


class CourseInfoSerializer(serializers.ModelSerializer):
    """课程信息序列化器：包含课程及教师、教材等信息"""
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = TeacherCourseClass  # 基于教师-课程-班级关联模型
        fields = ['id', 'course_name', 'description', 'teacher_name', 'textbook', 'syllabus', 'progress']

    # 获取课程名称
    course_name = serializers.CharField(source='course.name')
    # 获取课程描述等直接来源于关联的Course
    description = serializers.CharField(source='course.description', allow_null=True)
    textbook = serializers.CharField(source='course.textbook', allow_null=True)
    syllabus = serializers.CharField(source='course.syllabus', allow_null=True)
    progress = serializers.CharField()  # 来自 TeacherCourseClass 自身

    def get_teacher_name(self, obj):
        # 假设teacher是User模型，使用get_full_name或username作为姓名
        teacher = obj.teacher
        if hasattr(teacher, "get_full_name"):
            name = teacher.get_full_name()
        else:
            name = getattr(teacher, "name", None) or teacher.username
        return name


class AssignmentListSerializer(serializers.ModelSerializer):
    """作业列表序列化器：结合学生提交信息动态生成状态、分数和评语"""
    status = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    teacher_comment = serializers.SerializerMethodField()
    # 作业标题和截止日期直接序列化
    title = serializers.CharField()
    due_date = serializers.DateTimeField()

    class Meta:
        model = Assignment
        fields = ['id', 'title', 'due_date', 'status', 'score', 'teacher_comment']

    def get_status(self, obj):
        user = self.context['request'].user
        # 获取当前学生的提交记录
        submission = obj.submissions.filter(student=user).first()
        if not submission:
            return "未提交"
        if submission.is_returned:
            return "被退回"
        if submission.score is not None:
            return "已批改"
        # 提交存在且未评分未退回
        return "已提交"

    def get_score(self, obj):
        # 若已批改则返回分数，否则为空
        user = self.context['request'].user
        submission = obj.submissions.filter(student=user).first()
        return submission.score if submission and submission.score is not None else None

    def get_teacher_comment(self, obj):
        user = self.context['request'].user
        submission = obj.submissions.filter(student=user).first()
        return submission.teacher_comment if submission and submission.teacher_comment else None


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    """作业提交序列化器：用于学生提交作业和查看提交"""
    # 提交包含的附件文件列表，输出时序列化为{name, url}字典列表
    files = serializers.SerializerMethodField()
    # 上传文件时，接受一个文件列表字段（write_only，只用于反序列化提交）
    upload_files = serializers.ListField(
        child=serializers.FileField(max_length=10 * 1024 * 1024, allow_empty_file=True),  # 单个文件大小限制10MB
        write_only=True,
        allow_empty=True,
        required=False,
        # source='files'  # 暂存上传的文件列表
    )

    student_name = serializers.CharField(source='student.name', read_only=True, default='')  # 添加学生姓名
    student_number = serializers.CharField(source='student.student_number', read_only=True, default='')  # 添加学号

    class Meta:
        model = AssignmentSubmission
        fields = [
            'id', 'assignment', 'student', 'student_name', 'student_number',  # 添加student, student_name, student_number
            'title', 'content', 'upload_files', 'files',
            'score', 'teacher_comment', 'is_returned', 'submitted',
            'submit_time',  # 确保 submit_time 在
            # 新增AI相关字段 (如果模型已添加)
            'ai_comment', 'ai_score', 'ai_generated_similarity',
            'ai_grading_status', 'ai_grading_task_id'
        ]
        read_only_fields = [
            'student', 'student_name', 'student_number',  # student应只读，通过perform_create设置
            'files', 'submit_time',
            # AI结果字段也应该是只读的，由系统更新
            'ai_comment', 'ai_score', 'ai_generated_similarity',
            'ai_grading_status', 'ai_grading_task_id'
        ]
        extra_kwargs = {  # 确保 student 字段在创建时不强制要求，它将从 request.user 获取
            'student': {'required': False}
        }

    def get_files(self, obj):
        """序列化提交关联的附件文件列表"""
        files = []
        for f in obj.files.all():
            # 构造每个文件的访问URL和原始名称
            # 假设 settings 中配置了 MinIO 的外部访问URL 和 bucket 名称
            from django.conf import settings
            base_url = settings.MINIO_ENDPOINT
            if not base_url.startswith("http"):
                base_url = "http://" + base_url
            base_url = base_url.rstrip('/')
            bucket = getattr(settings, 'MINIO_BUCKET_NAME', '')
            if bucket:
                bucket = bucket.strip('/')
            file_url = f"{base_url}/{bucket}/{f.file_name}" if bucket else f"{base_url}/{f.file_name}"
            files.append({
                "name": f.original_name,
                "url": file_url
            })
        return files


class StudentDashboardSerializer(serializers.ModelSerializer):
    course_count = serializers.SerializerMethodField()
    pending_assignments = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()
    recent_courses = serializers.SerializerMethodField()
    class_name = serializers.CharField(source='class_enrolled.name')
    material_count = serializers.SerializerMethodField()
    latest_assignments = serializers.SerializerMethodField()

    class Meta:
        model = User  # 假设User模型有class_enrolled属性
        fields = [
            'student_number', 'name', 'class_name',
            'course_count', 'pending_assignments', 'avg_score', 'recent_courses', 'material_count', 'latest_assignments'
        ]

    def get_material_count(self, obj):
        # 计算该班级的教材数量
        return Material.objects.filter(teaching_class__class_obj=obj.class_enrolled).count()

    def get_course_count(self, obj):
        return TeacherCourseClass.objects.filter(class_obj=obj.class_enrolled).count()

    def get_pending_assignments(self, obj):
        from .models import Assignment

        all_ass_ids = Assignment.objects.filter(
            course_class__class_obj=obj.class_enrolled,
            due_date__gt=timezone.now()
        ).values_list('id')
        submited = AssignmentSubmission.objects.filter(
            assignment_id__in=list(all_ass_ids), is_returned=False
        )
        pending = len(all_ass_ids) - len(submited)
        return pending

    def get_latest_assignments(self, obj):
        """获取最新发布的 5 次作业 Homework"""
        from .models import Assignment
        last_ass = Assignment.objects.filter(
            course_class__class_obj=obj.class_enrolled,
            active=True
        ).order_by('-update_time')[:5]
        as_lis = []
        for as_dic in last_ass.values():
            if AssignmentSubmission.objects.filter(assignment_id=as_dic['id']):
                as_dic['submitted'] = True
            else:
                as_dic['submitted'] = False
            as_lis.append(as_dic)
        return as_lis

    def get_avg_score(self, obj):
        from .models import AssignmentSubmission
        avg = AssignmentSubmission.objects.filter(
            student=obj,
            score__isnull=False
        ).aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0.0  # 默认返回 0.0 而非 None

    def get_recent_courses(self, obj):
        courses = TeacherCourseClass.objects.filter(
            class_obj=obj.class_enrolled
        ).order_by('-start_date')[:5]
        return [{
            'id': c.id,
            'course_name': c.course.name,
            'teacher_name': c.teacher.get_full_name()
        } for c in courses]


class StudentCourseCardSerializer(serializers.ModelSerializer):
    """学生端课程卡片信息（基于 TeacherCourseClass）"""
    name = serializers.CharField(source='course.name')
    credit = serializers.DecimalField(source='course.credit', max_digits=4, decimal_places=1)
    hours = serializers.IntegerField(source='course.hours')
    teacher_name = serializers.CharField(source='teacher.get_full_name', default=None)

    class Meta:
        model = TeacherCourseClass
        fields = ['id', 'name', 'credit', 'hours', 'teacher_name']


class StudentCourseDetailSerializer(serializers.ModelSerializer):
    """
    学生课程详情页使用的序列化器，提供更丰富的课程信息。
    基于 TeacherCourseClass 模型。
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_description = serializers.CharField(source='course.description', read_only=True, allow_blank=True,
                                               allow_null=True)
    credit = serializers.DecimalField(source='course.credit', max_digits=4, decimal_places=1, read_only=True)
    hours = serializers.IntegerField(source='course.hours', read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)  # 使用 SerializerMethodField 以便处理教师姓名可能为空的情况

    # 直接从 TeacherCourseClass 模型获取的字段
    # textbook, syllabus, progress, start_date, end_date
    # create_time, update_time (可选, 如果前端需要显示)

    class Meta:
        model = TeacherCourseClass
        fields = [
            'id',  # TeacherCourseClass ID
            'course_name',
            'course_description',
            'credit',
            'hours',
            'teacher_name',
            'textbook',
            'syllabus',
            'progress',
            'start_date',
            'end_date',
            # 'start_week', 'end_week', # 如果需要，可以添加这些字段
            # 'course', # 可选，如果前端需要原始 course ID
            # 'class_obj', # 可选，如果前端需要原始 class_obj ID
            # 'teacher', # 可选，如果前端需要原始 teacher ID
        ]
        read_only_fields = fields  # 因为这是学生端的只读详情

    def get_teacher_name(self, obj):
        if obj.teacher:
            # 优先使用真实姓名，其次是用户名
            return obj.teacher.name or obj.teacher.username
        return "暂无教师信息"
