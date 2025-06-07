import os
from django.utils import timezone

import httpx
import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Avg, Q

from course.models import Assignment, AssignmentSubmission, TeacherCourseClass
from notifications.models import Notification

User = get_user_model()

logger = logging.getLogger(__name__)
AI_TEACHER_USERNAMES = ['teacherDeepseek', 'teacherDeepseekR']
MAX_CONTEXT_CHARS = 8000  # 上下文最大字符数，用于估算Token


def get_sender_context(user: User) -> str:
    """根据用户角色，抓取并格式化其个人背景信息。"""
    context_parts = [
        f"## 提问者信息\n- **身份**: {user.get_role_display()}\n- **用户名**: {user.username}\n- **姓名**: {user.name or '未设置'}"]

    if user.role == 'student':
        context_parts.append("\n### 学业概况")
        if user.class_enrolled:
            context_parts.append(f"- **班级**: {user.class_enrolled.name}")
            courses = TeacherCourseClass.objects.filter(class_obj=user.class_enrolled).select_related('course',
                                                                                                      'teacher')
            if courses.exists():
                context_parts.append("- **在修课程**: " + ", ".join(
                    [f"{c.course.name} ({c.teacher.name or c.teacher.username})" for c in courses]))

            submissions_objs = AssignmentSubmission.objects.filter(student=user)
            submissions = []
            for submission in submissions_objs:
                data = {
                    'assignment': {
                        'deployer': submission.assignment.deployer.username if submission.assignment.deployer else '未知',
                        'due_date': submission.assignment.due_date,
                        'description': submission.assignment.description,
                        'title': submission.assignment.title,
                    },
                    'score': submission.score,
                    'content': submission.content,
                    'submitted': submission.submitted,
                    'submit_time': submission.submit_time,
                    'teacher_comment': submission.teacher_comment,
                    'is_returned': submission.is_returned,
                    'ai_comment': submission.ai_comment,
                    'ai_score': submission.ai_score,
                    'ai_generated_similarity': submission.ai_generated_similarity,
                }
                submissions.append(data)
            submission_count = submissions_objs.count()
            avg_score = submissions_objs.filter(score__isnull=False).aggregate(avg=Avg('score'))['avg']
            context_parts.append(
                f"- **作业统计**: 共提交 {submission_count} 次, 平均分 {avg_score:.1f}" if avg_score else f"- **作业统计**: 共提交 {submission_count} 次")
            context_parts.append(
                "- **最近提交的作业**: " + ", ".join(
                    [f"{s['assignment']['title']} (分数: {s['score']}, 提交时间: {s['submit_time']})" for s in
                     submissions]))
        else:
            context_parts.append("- **班级**: 暂未分配")

    elif user.role == 'teacher':
        context_parts.append("\n### 执教概况")
        tccs = TeacherCourseClass.objects.filter(teacher=user).select_related('course', 'class_obj')
        if tccs.exists():
            context_parts.append("- **教授课程与班级**:")
            for tcc in tccs[:5]:  # 为节省Token，最多显示5条
                assignment_count = Assignment.objects.filter(course_class=tcc).count()
                context_parts.append(f"  - {tcc.course.name} ({tcc.class_obj.name})，已布置作业 {assignment_count} 次")
        else:
            context_parts.append("- **教授课程与班级**: 暂无")

    # 抓取历史交流信息，并控制长度
    context_parts.append("\n### 历史交流记录 (最近)")
    history_chars_so_far = sum(len(p) for p in context_parts)

    ai_teachers = User.objects.filter(username__in=AI_TEACHER_USERNAMES)
    recent_messages = Notification.objects.filter(
        (Q(sender=user, recipient__in=ai_teachers) | Q(sender__in=ai_teachers, recipient=user))
    ).order_by('-timestamp')[:10]

    history_log = []
    current_history_chars = 0
    for msg in reversed(recent_messages):
        role_map = {'student': '学生', 'teacher': '教师'}
        sender_role_display = "AI助教" if msg.sender.username in AI_TEACHER_USERNAMES else role_map.get(msg.sender.role,
                                                                                                        '用户')
        line = f"- **[{sender_role_display}]**: {msg.content}"

        # 估算Token，避免上下文过长
        if (history_chars_so_far + current_history_chars + len(line)) > MAX_CONTEXT_CHARS:
            break

        history_log.append(line)
        current_history_chars += len(line)

    if history_log:
        context_parts.extend(history_log)
    else:
        context_parts.append("- 暂无交流历史")

    return "\n".join(context_parts)


def find_all_messages_for_ai_teacher():
    """
    查找所有需要AI助教处理的消息。
    目前假设所有发给AI助教的私信都需要处理。
    """
    ai_teacher_ids = User.objects.filter(username__in=AI_TEACHER_USERNAMES).values_list('id', flat=True)
    return Notification.objects.filter(recipient__in=ai_teacher_ids, is_read=False).order_by(
        '-timestamp')[:3]


@shared_task(bind=True, name="notifications.tasks.process_ai_teacher_message", default_retry_delay=60, max_retries=3)
def process_ai_teacher_message(self):
    """
    Celery task to process a message sent to an AI teacher.
    """
    for user_message in find_all_messages_for_ai_teacher():
        sender = user_message.sender
        ai_teacher_user = user_message.recipient
        original_title = user_message.title

        # 1. 收集上下文并构建Prompt
        context = get_sender_context(sender)
        system_prompt = (
            f"你是一位资深、有耐心、善于启发学生的AI助教老师。你的名字是 {ai_teacher_user.name or ai_teacher_user.username}。"
            "你的目标是根据用户提供的背景信息和历史交流，以富有人情味和启发性的方式回答本次问题，而不是直接给出最终答案。"
            "请总是尝试引导用户自己思考。请直接回复内容，不要进行额外确认。"
        )
        user_prompt_for_ai = f"{context}\n\n## 本次问题\n**标题**: {original_title}\n**内容**: {user_message.content}"

        # 2. 估算Token并截断
        if len(system_prompt) + len(user_prompt_for_ai) > 10000:
            logger.warning(f"AI prompt for user {sender.username} exceeds token limit estimation. Truncating.")
            user_prompt_for_ai = user_prompt_for_ai[:10000 - len(system_prompt)]

        # 3. 判断使用哪个模型
        use_reasoning_model = (ai_teacher_user.username == 'teacherDeepseekR')

        # 4. 调用AI服务
        ai_service_url = os.getenv('AI_SERVICE_URL', 'http://localhost:8080/api/v1/chat/completions')
        payload = {
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt_for_ai}],
            "use_reasoning_model": use_reasoning_model,
        }

        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(ai_service_url, json=payload)
                response.raise_for_status()
                ai_response_data = response.json()

            if ai_response_data.get("success") and ai_response_data.get("content"):
                ai_content = ai_response_data["content"]
            else:
                ai_content = f"抱歉，AI助教暂时无法连接，请稍后再试。错误: {ai_response_data.get('error', '未知错误')}"
                logger.error(f"AI service call failed for user {sender.id}: {ai_response_data.get('error')}")

        except Exception as e:
            logger.error(f"Failed to communicate with AI service for user {sender.id}: {e}", exc_info=True)
            # 如果调用失败，自动重试
            raise self.retry(exc=e)

        # 5. 将AI的回复作为新消息存入数据库
        Notification.objects.create(
            recipient=sender,
            sender=ai_teacher_user,
            type='private_message',
            title=f"Re: {original_title}",
            content=ai_content,
            parent_notification=user_message,
            can_recipient_delete=True,
            can_recipient_reply=True,
        )

        # 6. 标记原消息为已读
        user_message.is_read = True
        user_message.read_at = timezone.now()
        user_message.save()

