from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class Class(models.Model):
    """
    班级模型，用于归属学生（一个班级可以有多个学生），
    同时被 TeacherCourseClass 用来与课程、教师进行三方关联。
    """
    name = models.CharField(
        max_length=100,
        verbose_name="班级名称"
    )
    major = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="专业"
    )
    department = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="院系"
    )
    year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="年份/届别"
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="班级描述"
    )

    def __str__(self):
        # 显示班级名称和届别
        return f"{self.name} - {self.year or ''}"


class User(AbstractUser):
    """
    自定义用户模型，扩展了角色(role)字段、学号(student_number)以及学生所属班级(class_enrolled)。
    - admin: 超级管理员
    - teacher: 教师
    - student: 学生
    学生只能属于一个班级；教师和管理员一般不需要关联班级。
    """
    ROLE_CHOICES = [
        ('superadmin', "Super Admin"),  # 超级管理员
        ('admin', "Admin"),  # 超级管理员
        ('teacher', "Teacher"),  # 教师
        ('student', "Student")  # 学生
    ]

    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    ]

    # 学生/教师/管理员的真实姓名，可选
    name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="真实姓名"
    )
    # 学生所属班级：仅当role='student'时才有效
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    teacher_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    student_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    qq = models.CharField(max_length=15, null=True, blank=True)
    class_enrolled = models.ForeignKey(
        'Class',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    class Meta:
        ordering = ['student_number']

    def __str__(self):
        return f"{self.username} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'


class Course(models.Model):
    """
    课程基本信息模型
    - 由超级管理员创建并设置课程名称、学分、课时等基础信息
    - 与班级和教师的关联由 TeacherCourseClass 管理
    """
    name = models.CharField(
        max_length=100,
        verbose_name="课程名称"
    )
    description = models.TextField(
        blank=True,
        verbose_name="课程描述"
    )
    credit = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0,
        verbose_name="学分"
    )
    hours = models.IntegerField(
        default=0,
        verbose_name="课时"
    )
    # 保留一个多对多字段用于记录哪些教师可教授此课程（可选）
    # 如需严格区分班级，可在 TeacherCourseClass 中再做限制
    teachers = models.ManyToManyField(
        User,
        related_name="teaching_courses",
        verbose_name="任课教师",
        limit_choices_to={'role': 'teacher'},
        blank=True
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    def __str__(self):
        return self.name


# 只保留下面这一个 Material，或者把你需要的字段合并到它
class Material(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('lecture', '课件'),
        ('example', '教学示例'),
        ('software', '软件安装包'),
        ('reference', '参考资料'),
        ('other', '其他')
    ]

    title = models.CharField(max_length=100, verbose_name="资料标题")
    file = models.FileField(upload_to="materials/", verbose_name="文件路径")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="上传者")
    teaching_class = models.ForeignKey(
        'course.TeacherCourseClass',
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name="所属教学班",
        default=None
    )
    material_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPE_CHOICES,
        default='other',
        verbose_name="资源类型"
    )
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    def __str__(self):
        return f"{self.teaching_class.course.name} - {self.title}"


class TeacherCourseClass(models.Model):
    """
    教师-课程-班级 三方关联模型：
      - 每个TeacherCourseClass代表了某位教师在某个班级教授某门课程
      - 用来做数据隔离：同一门课在不同班级由同或不同教师教授时，其作业、资料等互不影响
    """
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="teaching_assignments",
        verbose_name="教师",
        limit_choices_to={'role': 'teacher'}
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="teaching_arrangements",
        verbose_name="课程"
    )
    class_group = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="course_arrangements",
        verbose_name="班级"
    )
    textbook = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="使用教材"
    )
    syllabus = models.TextField(
        blank=True,
        null=True,
        verbose_name="教学大纲"
    )
    progress = models.TextField(
        blank=True,
        null=True,
        verbose_name="教学进度"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    class Meta:
        unique_together = ('teacher', 'course', 'class_group')
        verbose_name = "教师课程班级关联"
        verbose_name_plural = "教师课程班级关联"

    def __str__(self):
        return f"{self.teacher.username}教授{self.class_group.name}的{self.course.name}课程"


class Announcement(models.Model):
    """
    公告模型
    - author: 发布者（教师或管理员）
    - target_classes: 公告目标班级，多对多关系，可同时选择多个班级
    - 学生可在 AnnouncementRead 中记录已读情况
    """
    title = models.CharField(
        max_length=200,
        verbose_name="公告标题"
    )
    content = models.TextField(
        verbose_name="公告内容"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="发布者"
    )
    # 公告可面向多个班级
    target_classes = models.ManyToManyField(
        Class,
        related_name="announcements",
        verbose_name="目标班级"
    )
    publish_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="发布时间"
    )

    def __str__(self):
        return f"{self.title} ({self.publish_time.date()})"


class AnnouncementRead(models.Model):
    """
    学生公告已读表，用于记录哪些学生在何时阅读了某个公告
    """
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="reads",
        verbose_name="公告"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="announcement_reads",
        limit_choices_to={'role': 'student'},
        verbose_name="学生"
    )
    read_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="已读时间"
    )

    def __str__(self):
        return f"{self.student.username} read {self.announcement.title}"


class Assignment(models.Model):
    """
    作业模型
    - 关联TeacherCourseClass，实现对某个(教师+课程+班级)的作业下发
    - 可选附件，启用AI批改的标志与模板
    """
    title = models.CharField(
        max_length=200,
        verbose_name="作业标题"
    )
    description = models.TextField(
        verbose_name="作业描述"
    )
    teaching_class = models.ForeignKey(
        TeacherCourseClass,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="所属教学班"
    )
    due_date = models.DateTimeField(
        verbose_name="截止日期"
    )
    attachment = models.FileField(
        upload_to="assignments/",
        null=True,
        blank=True,
        verbose_name="附件文件"
    )
    ai_grading_enabled = models.BooleanField(
        default=False,
        verbose_name="启用AI批改"
    )
    ai_prompt_template = models.TextField(
        null=True,
        blank=True,
        verbose_name="AI批改提示模板"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="发布时间"
    )

    def __str__(self):
        return f"{self.teaching_class.course.name} - {self.title}"


class AssignmentSubmission(models.Model):
    """
    学生提交作业表
    - assignment: 对应某一教学班发布的一道作业
    - student: 提交的学生
    - 包含文本内容或附件，评分及评语
    """
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="作业"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submissions",
        limit_choices_to={'role': 'student'},
        verbose_name="学生"
    )
    content = models.TextField(
        null=True,
        blank=True,
        verbose_name="提交内容"
    )
    file = models.FileField(
        upload_to="submissions/",
        null=True,
        blank=True,
        verbose_name="提交附件"
    )
    submit_time = models.DateTimeField(
        auto_now=True,
        verbose_name="提交时间"
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="评分"
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        verbose_name="评语"
    )
    grade_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="批改时间"
    )

    class Meta:
        # 限制 assignment 与 student 的组合必须唯一，避免重复提交记录
        unique_together = (("assignment", "student"),)

    def __str__(self):
        return f"Submission({self.assignment.title} - {self.student.username})"


class BlogPost(models.Model):
    """
    博客/帖子模型：
    - author: 发帖人，可为教师或学生
    - content: 帖子内容
    """
    title = models.CharField(
        max_length=200,
        verbose_name="标题"
    )
    content = models.TextField(
        verbose_name="正文"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blog_posts",
        verbose_name="作者"
    )
    publish_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="发布时间"
    )
    update_time = models.DateTimeField(
        auto_now=True,
        verbose_name="最后修改时间"
    )

    def __str__(self):
        return self.title


class BlogComment(models.Model):
    """
    评论模型：支持两级嵌套（parent 指向父评论, 为空则为一级评论）
    """
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="所属帖子"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="评论者"
    )
    content = models.TextField(
        verbose_name="评论内容"
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="父评论"
    )
    publish_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="评论时间"
    )

    def __str__(self):
        return f"Comment by {self.author.username}: {self.content[:20]}..."


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_notification_settings(sender, instance, created, **kwargs):
    if created:
        from notifications.models import UserNotificationSettings  # 延迟导入
        UserNotificationSettings.objects.create(user=instance)
    # 如果 UserNotificationSettings 包含需要从 User 模型同步的字段，可以在这里更新
    # instance.notifications_settings.save() # 如果有需要同步的字段
