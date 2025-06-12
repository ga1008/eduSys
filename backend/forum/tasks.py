# backend/forum/tasks.py

import httpx
import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # bind=True 以便使用 self.retry
def trigger_ai_comment(self, post_id):
    """
    触发AI为帖子生成评论。
    此任务参考 notifications/tasks.py 的实现，使用 httpx 直接调用 AI 服务。
    """
    try:
        post = Post.objects.select_related('author', 'author__class_enrolled').get(id=post_id)
        author = post.author
    except Post.DoesNotExist:
        logger.warning(f"Post with id {post_id} does not exist. AI comment task cancelled.")
        return

    # 1. 准备向AI服务发送的基础信息
    if post.is_anonymous:
        user_info = "一位匿名同学"
    else:
        courses = post.author.student_tcc.select_related('course').all()
        courses_info = ", ".join([tcc.course.name for tcc in courses]) or "暂无"
        user_info = (
            f"学生姓名: {author.real_name}, "
            f"班级: {author.class_enrolled.name if author.class_enrolled else '未分配'}, "
            f"所学课程: {courses_info}"
        )

    # 2. 构造 System Prompt 和 User Prompt
    system_prompt = "你是一个在线教育平台的AI助教。你的任务是为学生的帖子生成一段有帮助的、积极友善的评论，以鼓励讨论和学习。"
    user_prompt_for_ai = (
        f"请为以下帖子生成评论：\n"
        f"---提问者信息---\n{user_info}\n"
        f"---帖子信息---\n"
        f"标题: {post.title}\n"
        f"内容: {post.content}\n"
        f"---请根据以上信息，撰写你的评论---"
    )

    # 3. 使用 httpx 直接调用 AI 服务 (与 notifications/tasks.py 逻辑相同)
    ai_service_url = settings.AI_SERVICE_URL
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_for_ai}
        ],
        "use_reasoning_model": False,  # 论坛评论通常不需要最强模型
    }

    ai_content = ""
    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(ai_service_url, json=payload)
            response.raise_for_status()
            ai_response_data = response.json()

        if ai_response_data.get("success") and ai_response_data.get("content"):
            ai_content = ai_response_data["content"]
        else:
            error_msg = ai_response_data.get('error', '未知错误')
            ai_content = f"抱歉，AI助教暂时无法连接，请稍后再试。错误: {error_msg}"
            logger.error(f"AI service call failed for post {post_id}: {error_msg}")

    except Exception as e:
        logger.error(f"Failed to communicate with AI service for post {post_id}: {e}", exc_info=True)
        # 如果调用失败，使用celery的重试机制
        raise self.retry(exc=e)

    # 4. 创建 AI 评论，记录结果
    if ai_content:
        Comment.objects.create(
            post=post,
            author=author,  # 逻辑上将AI评论的author记为帖子作者，方便管理
            content=ai_content,
            is_anonymous=False,
            is_ai_generated=True
        )
        # 更新帖子评论数
        post.comment_count = post.comments.count()
        post.save(update_fields=['comment_count'])
