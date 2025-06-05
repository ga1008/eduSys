# backend/course/models.py
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings  # 假设 settings.AUTH_USER_MODEL 作为 User 模型
from django.db.models.signals import post_save
from django.dispatch import receiver

from education.models import Class


class Course(models.Model):
    name = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=1)  # 学分，可为整数或一位小数
    hours = models.IntegerField()  # 总课时
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=20, default=None)  # 课程代码，唯一
    # 多对多关联到 Class，通过 TeacherCourseClass 中间模型
    classes = models.ManyToManyField('education.Class', through='TeacherCourseClass', related_name='courses')

    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)  # 更新时间

    def __str__(self):
        return self.name


class TeacherCourseClass(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    class_obj = models.ForeignKey('education.Class', on_delete=models.CASCADE)
    teacher = models.ForeignKey('education.User', on_delete=models.CASCADE)
    textbook = models.CharField(max_length=200, blank=True, null=True)  # 教材
    syllabus = models.TextField(blank=True, null=True)  # 教学大纲
    progress = models.TextField(blank=True, null=True)  # 教学进度
    start_date = models.DateField(null=True, blank=True)  # 开课日期
    end_date = models.DateField(null=True, blank=True)  # 结课日期
    start_week = models.IntegerField(null=True, blank=True)  # 开课周
    end_week = models.IntegerField(null=True, blank=True)  # 结课周

    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)  # 更新时间

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "class_obj"], name="unique_course_class")
        ]
        verbose_name = "教学班关联"

    def __str__(self):
        return f"{self.course.name} - {self.class_obj.name} ({self.teacher.get_full_name()})"


class Assignment(models.Model):
    course_class = models.ForeignKey(TeacherCourseClass, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)  # 作业标题
    description = models.TextField(blank=True, null=True)  # 作业描述，支持富文本
    due_date = models.DateTimeField()  # 截止日期
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)  # 默认满分100
    deploy_date = models.DateTimeField(auto_now_add=True)  # 发布日期
    deployer = models.ForeignKey('education.User', on_delete=models.CASCADE)  # 发布人

    active = models.BooleanField(default=True)  # 是否启用作业

    ai_grading_enabled = models.BooleanField(default=False, verbose_name="启用AI辅助批改")
    ai_grading_prompt = models.TextField(blank=True, null=True, verbose_name="AI辅助批改提示词")

    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)  # 更新时间

    def __str__(self):
        return self.title


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey('education.User', on_delete=models.CASCADE)  # 提交的学生用户
    title = models.CharField(max_length=100)  # 提交的标题（学生填写）
    content = models.TextField()  # 提交的正文（富文本存储HTML）
    score = models.IntegerField(null=True, blank=True)  # 教师评分
    teacher_comment = models.TextField(null=True, blank=True)  # 教师评语
    is_returned = models.BooleanField(default=False)  # 是否被退回要求重交
    submit_time = models.DateTimeField(auto_now_add=True)
    submitted = models.BooleanField(default=True)  # 是否已提交

    # 新增字段用于AI批改
    ai_comment = models.TextField(null=True, blank=True, verbose_name="AI评语")
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="AI评分")
    ai_generated_similarity = models.FloatField(null=True, blank=True, verbose_name="AI生成疑似度")
    ai_grading_status = models.CharField(max_length=20,
                                         choices=[
                                             ('pending', '待处理'),
                                             ('processing', '处理中'),
                                             ('completed', '已完成'),
                                             ('failed', '失败'),
                                             ('skipped', '已跳过')
                                         ],
                                         default='pending', null=True, blank=True, verbose_name="AI批改状态")
    ai_grading_task_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="AI批改任务ID")

    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)  # 更新时间

    def __str__(self):  # 确保有__str__方法
        return f"Submission by {self.student.username} for {self.assignment.title}"


# 为支持多个附件文件，我们新增一个附件模型
class AssignmentSubmissionFile(models.Model):
    submission = models.ForeignKey(AssignmentSubmission, on_delete=models.CASCADE, related_name="files")
    file_name = models.CharField(max_length=255)  # 文件对象名或路径（在存储中的名称）
    original_name = models.CharField(max_length=255)  # 原始文件名（用于显示）
    # 注：此处不直接使用FileField，以方便通过MinIO客户端自定义上传逻辑

    create_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # 创建时间
    update_time = models.DateTimeField(auto_now=True, null=True, blank=True)  # 更新时间


@receiver(post_save, sender=Assignment)  # 确保 Assignment 是您课程应用中的模型
def assignment_created_or_updated_notification(sender, instance, created, **kwargs):
    try:
        # 延迟导入 Notification 模型以避免循环依赖问题
        from notifications.models import Notification as NotificationModel
        from education.models import User as UserModel  #

        teacher_course_class = instance.course_class  #
        if not (teacher_course_class and hasattr(teacher_course_class, 'class_obj')):
            return

        target_class = teacher_course_class.class_obj
        students_in_class = UserModel.objects.filter(class_enrolled=target_class, role='student', is_active=True)  #

        assignment_content_type = ContentType.objects.get_for_model(instance)
        action_text = "发布了新作业" if created else "更新了作业"
        notification_type_str = 'assignment_new'  # 对学生而言，更新也视为新通知或重要更新

        for student in students_in_class:
            NotificationModel.objects.create(
                recipient=student,
                sender=instance.deployer,  # 布置作业的教师
                type=notification_type_str,
                title=f"作业{action_text}: {instance.title}",
                content=f"课程 '{teacher_course_class.course.name}' {action_text} '{instance.title}'。截止日期: {instance.due_date.strftime('%Y-%m-%d %H:%M') if instance.due_date else '未指定'}。",
                content_type=assignment_content_type,
                object_id=instance.id,
                can_recipient_delete=False,  # 学生不能删除作业通知
                can_recipient_reply=False
            )
    except Exception as e:
        # logger.error(f"创建作业通知时出错: {e}")
        print(f"创建作业通知时出错: {e}")


@receiver(post_save, sender=AssignmentSubmission)  # 确保 AssignmentSubmission 是您课程应用中的模型
def assignment_graded_or_submitted_notification(sender, instance, created, **kwargs):
    try:
        from notifications.models import Notification as NotificationModel
        submission_content_type = ContentType.objects.get_for_model(instance)

        if created and instance.submitted:  # 学生刚提交作业
            # 通知教师
            target_teacher = instance.assignment.deployer  # 作业的布置者
            if target_teacher:
                NotificationModel.objects.create(
                    recipient=target_teacher,
                    sender=instance.student,  # 学生是发送者
                    type='submission_new',
                    title=f"新作业提交: {instance.assignment.title}",
                    content=f"学生 {instance.student.name or instance.student.username} 提交了作业 '{instance.assignment.title}'。",
                    content_type=submission_content_type,
                    object_id=instance.id,
                    can_recipient_delete=True,  # 教师可删除此通知
                    can_recipient_reply=False  # 通常教师直接去批改系统操作
                )
        elif not created and 'score' in (kwargs.get('update_fields') or []) and instance.score is not None:
            # 作业被评分 (score字段更新且不为空)
            NotificationModel.objects.create(
                recipient=instance.student,
                sender=instance.assignment.deployer,  # 批改者通常是布置作业的教师
                type='assignment_graded',
                title=f"作业已批改: {instance.assignment.title}",
                content=f"您提交的作业 '{instance.assignment.title}' 已被批改。得分: {instance.score}。"
                        f"{(' 教师评语: ' + instance.teacher_comment) if instance.teacher_comment else ''}",
                content_type=submission_content_type,
                object_id=instance.id,
                can_recipient_delete=False,  # 学生不能删除成绩通知
                can_recipient_reply=False
            )
    except Exception as e:
        # logger.error(f"创建提交通知或批改通知时出错: {e}")
        print(f"创建提交通知或批改通知时出错: {e}")
