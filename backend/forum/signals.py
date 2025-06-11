# backend/forum/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment
from notifications.models import Notification


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        post_author = instance.post.author
        comment_author = instance.author

        # 如果评论者不是帖子作者，且不是AI自动回复，则创建通知
        if post_author != comment_author and not instance.is_ai_generated:
            message = f'您的帖子 "{instance.post.title}" 有了新的回复。'
            Notification.objects.create(
                recipient=post_author,
                message=message,
                notification_type='FORUM',
                # content_object=instance.post # GenericForeignKey, 可选
            )
