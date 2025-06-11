# backend/forum/tasks.py

from celery import shared_task
from .models import Post, Comment
from ai_service.app.tasks import generate_text  # 导入 ai_service 的任务


@shared_task
def trigger_ai_comment(post_id):
    try:
        post = Post.objects.get(id=post_id)
        author = post.author

        # 1. 准备基础信息
        if post.is_anonymous:
            user_info = "一位匿名同学"
        else:
            courses_info = ", ".join([tcc.course.name for tcc in author.student_tcc.all()])
            user_info = (
                f"学生姓名：{author.real_name}, "
                f"班级：{author.class_enrolled.name}, "
                f"所学课程：{courses_info}"
            )

        # 2. 构造 Prompt
        prompt = (
            f"你是一个在线教育平台的AI助教。请根据以下信息，为帖子生成一段有帮助的、友善的评论。\n"
            f"---用户信息---\n{user_info}\n"
            f"---帖子信息---\n"
            f"标题: {post.title}\n"
            f"内容: {post.content}\n"
            f"---请生成评论---"
        )

        # 3. 调用 AI 服务 (这是异步调用)
        # 注意：这里调用的是 ai_service 的 celery task
        ai_response_task = generate_text.delay(prompt)
        ai_response = ai_response_task.get(timeout=60)  # 等待AI服务返回结果

        # 4. 创建 AI 评论
        if ai_response:
            Comment.objects.create(
                post=post,
                author=author,  # 逻辑上将AI评论的author也记为帖子作者，方便管理
                content=ai_response,
                is_anonymous=False,  # AI评论不匿名
                is_ai_generated=True
            )
            # 更新帖子评论数
            post.comment_count = post.comments.count()
            post.save()

    except Post.DoesNotExist:
        # 处理帖子不存在的情况
        pass
    except Exception as e:
        # 处理可能的异常，例如AI服务超时
        print(f"Error generating AI comment for post {post_id}: {e}")
