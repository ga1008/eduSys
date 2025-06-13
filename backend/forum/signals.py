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

        # 如果是自己回复自己，或AI生成的评论，则不通知
        if post_author != comment_author and not instance.is_ai_generated:
            Notification.objects.create(
                recipient=post_author,
                sender=comment_author,
                type='forum_reply',  # 使用一个明确的类型
                title=f'您的帖子 "{instance.post.title}" 有了新回复',
                content=instance.content[:100],  # 截取部分内容作为预览
                related_object=instance.post  # 关联到原帖子
            )
