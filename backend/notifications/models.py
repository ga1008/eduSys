# notifications/models.py
from django.db import models
from django.conf import settings  # 用于 settings.AUTH_USER_MODEL
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone  # 引入 timezone


class Notification(models.Model):
    """
    核心模型，用于存储所有类型的通知，包括私信和系统提醒。
    """
    NOTIFICATION_TYPES = [
        # 私信
        ('private_message', '私信'),

        # 学生相关 (如果也适用于教师，则通用)
        ('assignment_new', '新作业发布'),
        ('assignment_graded', '作业已批改'),
        ('course_change', '课程信息更新'),  # 例如：课程详情、资料更新
        ('class_change', '班级信息更新'),  # 例如：学生加入/移出班级、班级详情变更
        ('forum_reply', '论坛新回复'),  # 回复了您的帖子或评论
        ('forum_like_summary', '论坛收到点赞'),  # 点赞汇总

        # 教师相关
        ('submission_new', '学生提交新作业'),  # 学生提交了作业

        # 系统 / 管理员
        ('system_announcement', '系统公告'),  # 管理员发给特定用户/角色的公告
        ('user_mention', '用户提及'),  # 如果实现 @提及 功能

        # 默认/其他
        ('other', '其他通知'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', verbose_name="接收者",
                                  on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_notifications', verbose_name="发送者",
                               null=True, blank=True, on_delete=models.SET_NULL)  # 系统生成的通知，发送者可以为Null

    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, verbose_name="通知类型")
    title = models.CharField(max_length=255, blank=True, null=True, verbose_name="通知标题")  # 可选的标题
    content = models.TextField(verbose_name="通知内容")  # 主要信息或描述
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="时间戳")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读时间")

    # 用于关联到特定对象 (例如：作业、课程、论坛帖子、另一个用户以建立消息上下文)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    # 基于通知类型和接收者角色的控制标志
    can_recipient_delete = models.BooleanField(default=True, verbose_name="接收者可删除")  # 接收者是否可以删除此通知？
    can_recipient_reply = models.BooleanField(default=False, verbose_name="接收者可回复")  # 这是否是一条可以直接回复的消息？

    # 用于消息会话 (简单实现：parent_notification 指向回复的原始消息)
    parent_notification = models.ForeignKey('self', null=True, blank=True, related_name='replies',
                                            verbose_name="父通知ID", on_delete=models.CASCADE)

    # 用于存储额外上下文信息的JSON字段 (例如：班级变更通知中的新旧班级名)
    data = models.JSONField(null=True, blank=True, verbose_name="附加数据")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "通知"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-timestamp']),
        ]

    def __str__(self):
        return f"接收者: {self.recipient.username} - 类型: {self.get_type_display()} - 是否已读: {self.is_read}"

    def mark_as_read(self):
        # 将通知标记为已读
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        # 将通知标记为未读
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])


class UserNotificationSettings(models.Model):
    """
    存储用户特定的通知偏好和屏蔽规则。
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='notification_settings', verbose_name="用户",
                                on_delete=models.CASCADE)

    # 通用接收开关
    receive_private_messages = models.BooleanField(default=True, verbose_name="接收私信")
    receive_assignment_notifications = models.BooleanField(default=True, verbose_name="接收作业相关通知")
    receive_grading_notifications = models.BooleanField(default=True, verbose_name="接收批改相关通知")
    receive_forum_notifications = models.BooleanField(default=True, verbose_name="接收论坛相关通知")
    receive_course_class_change_notifications = models.BooleanField(default=True, verbose_name="接收课程/班级变动通知")
    # 根据需要为特定通知类型添加更多开关

    # 私信屏蔽规则
    # 'everyone': 允许所有私信 (除非被单独拉黑)
    # 'contacts_only': 学生：仅允许老师、管理员、超级管理员。教师：仅允许管理员、超级管理员。 (简化，更细致的 "仅允许某些人" 可作为V2功能)
    # 'teachers_staff_only': 学生：仅允许老师、管理员、超级管理员。
    # 'staff_only': 教师：仅允许管理员、超级管理员。
    # 'superadmin_only': 仅允许超级管理员。
    # 'none': 屏蔽所有私信 (超级管理员的消息可能例外，根据具体逻辑判断)。
    PRIVATE_MESSAGE_POLICY_CHOICES = [
        ('everyone', '任何人'),
        ('contacts_only', '仅限指定联系人'),  # 用于更细致的控制
        ('teachers_staff_only', '仅限教师和管理员'),  # 学生用
        ('staff_only', '仅限管理员'),  # 教师用
        ('superadmin_only', '仅限超级管理员'),  # 教师/管理员用
        ('none', '不接收任何人私信 (超级管理员除外)'),
    ]
    private_message_policy = models.CharField(max_length=30, choices=PRIVATE_MESSAGE_POLICY_CHOICES, default='everyone',
                                              verbose_name="私信接收策略")

    # 如果策略是 'contacts_only'，则明确允许发送消息的用户列表
    # 为简化起见，明确的“允许列表”可以作为V2功能。
    # 我们首先依赖 `BlockedContact` 来实现明确的屏蔽。

    class Meta:
        verbose_name = "用户通知设置"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username} 的通知设置"


class BlockedContact(models.Model):
    """
    表示用户屏蔽来自另一用户的联系，主要用于私信。
    """
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking_contacts', verbose_name="屏蔽发起者",
                                on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by_contacts',
                                     verbose_name="被屏蔽者", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="屏蔽时间")

    class Meta:
        unique_together = ('blocker', 'blocked_user')  # 确保屏蔽关系唯一
        ordering = ['-timestamp']
        verbose_name = "黑名单联系人"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.blocker.username} 屏蔽了 {self.blocked_user.username}"
