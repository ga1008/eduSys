from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import httpx
import logging
import os

from .models import AssignmentSubmission, Assignment
# from .utils import extract_json_from_string # 确保此函数可用
# 复制或导入 extract_json_from_string
import re
import json
from typing import Optional


def extract_json_from_string(text_containing_json: str) -> Optional[dict]:
    try:
        match_triple_quotes = re.search(r"```json\s*(\{.*?\})\s*```", text_containing_json, re.DOTALL)
        if match_triple_quotes:
            json_str = match_triple_quotes.group(1)
        else:
            first_brace = text_containing_json.find('{')
            last_brace = text_containing_json.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = text_containing_json[first_brace: last_brace + 1]
            else:
                first_bracket = text_containing_json.find('[')
                last_bracket = text_containing_json.rfind(']')
                if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                    json_str = text_containing_json[first_bracket: last_bracket + 1]
                else:
                    return None

        json_str_cleaned = json_str.strip()
        parsed_json = json.loads(json_str_cleaned)
        return parsed_json
    except Exception:
        return None


logger = logging.getLogger(__name__)

# AI_SERVICE_STATUS_URL = "http://localhost:8080/api/v1/task_status/" # 应从settings读取
AI_SERVICE_STATUS_URL = os.getenv('AI_SERVICE_STATUS_URL', 'http://localhost:8080/api/v1/task_status/')


@shared_task(name="course.tasks.check_ai_grading_results", bind=True, default_retry_delay=5 * 60, max_retries=3)
def check_ai_grading_results(self):
    # 查找1小时内仍在处理中的，且有task_id的提交
    # time_threshold = timezone.now() - timedelta(hours=1) # 避免查询过旧的任务
    # submissions_to_check = AssignmentSubmission.objects.filter(
    #     ai_grading_status='processing',
    #     ai_grading_task_id__isnull=False,
    #     update_time__gte=time_threshold # 只检查最近更新的
    # )

    # 简单起见，先检查所有 processing 状态的
    submissions_to_check = AssignmentSubmission.objects.filter(
        ai_grading_status='processing',
        ai_grading_task_id__isnull=False
    )

    logger.info(f"Found {submissions_to_check.count()} submissions to check AI grading status.")

    for submission in submissions_to_check:
        if not submission.ai_grading_task_id:
            continue

        task_status_url = f"{AI_SERVICE_STATUS_URL.rstrip('/')}/{submission.ai_grading_task_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(task_status_url)

            if response.status_code == 200:
                ai_api_response = response.json()
                if ai_api_response.get("success") and ai_api_response.get("content"):  # 任务完成且成功
                    raw_ai_output = ai_api_response.get("content")
                    parsed_json_result = extract_json_from_string(raw_ai_output)

                    assignment = submission.assignment  # 获取关联的作业以得到max_score

                    if parsed_json_result and "score" in parsed_json_result and "comment" in parsed_json_result:
                        submission.ai_score = parsed_json_result.get("score")
                        # 确保分数不超过满分
                        if submission.ai_score is not None and assignment.max_score is not None:
                            try:
                                ai_s = float(submission.ai_score)
                                max_s = float(assignment.max_score)
                                submission.ai_score = min(max(0, ai_s), max_s)
                            except ValueError:
                                logger.error(
                                    f"Invalid score format from AI for submission {submission.id}: {submission.ai_score}")
                                submission.ai_score = None  # 或标记为解析失败

                        submission.ai_comment = parsed_json_result.get("comment")
                        submission.ai_generated_similarity = parsed_json_result.get("AI生成疑似度")
                        submission.ai_grading_status = 'completed'
                        logger.info(
                            f"AI grading completed for submission {submission.id}. Score: {submission.ai_score}")
                    else:
                        submission.ai_grading_status = 'failed'
                        submission.ai_comment = f"AI返回结果解析失败或缺少字段。原始输出: {raw_ai_output[:500]}"
                        logger.error(f"AI result parsing failed for submission {submission.id}. Raw: {raw_ai_output}")
                    submission.save()
                elif ai_api_response.get("error") and "Task not ready" not in ai_api_response.get("error"):  # 任务失败
                    submission.ai_grading_status = 'failed'
                    submission.ai_comment = f"AI批改任务失败: {ai_api_response.get('error')}"
                    submission.save(update_fields=['ai_grading_status', 'ai_comment'])
                    logger.warning(
                        f"AI grading task {submission.ai_grading_task_id} failed for submission {submission.id}: {ai_api_response.get('error')}")
                # else: 任务仍在处理中或AI服务返回了非预期的成功格式

            elif response.status_code == 404:  # Task ID 在AI服务侧可能不存在了
                submission.ai_grading_status = 'failed'
                submission.ai_comment = f"AI批改任务ID {submission.ai_grading_task_id} 在AI服务中未找到。"
                submission.save(update_fields=['ai_grading_status', 'ai_comment'])
                logger.error(
                    f"AI Task ID {submission.ai_grading_task_id} not found on AI service for submission {submission.id}.")
            else:
                logger.error(
                    f"Failed to get status for task {submission.ai_grading_task_id} (submission {submission.id}). Status: {response.status_code}, Body: {response.text[:200]}")
                # 可以考虑重试此特定提交的检查

        except httpx.TimeoutException:
            logger.warning(
                f"Timeout checking AI task status for submission {submission.id}, task {submission.ai_grading_task_id}.")
            # 任务可能会在下次检查时成功
        except httpx.RequestError as e:
            logger.error(
                f"Request error checking AI task status for submission {submission.id}, task {submission.ai_grading_task_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error checking AI task status for sub {submission.id}: {e}", exc_info=True)
            try:  # 尝试将 submission 标记为失败，避免无限重试
                submission.ai_grading_status = 'failed'
                submission.ai_comment = f"检查AI批改结果时发生内部错误: {str(e)[:100]}"
                submission.save(update_fields=['ai_grading_status', 'ai_comment'])
            except Exception as save_err:
                logger.error(f"Failed to save error status for submission {submission.id}: {save_err}")


@shared_task(name="course.tasks.cleanup_old_processing_ai_submissions")
def cleanup_old_processing_ai_submissions():
    """
    清理那些长时间处于 'processing' 状态但可能已失败或丢失的AI批改任务。
    例如，超过2小时仍在 processing 状态的，可以标记为 failed。
    """
    time_threshold = timezone.now() - timedelta(hours=2)  # 2小时阈值
    stuck_submissions = AssignmentSubmission.objects.filter(
        ai_grading_status='processing',
        update_time__lt=time_threshold  # update_time 是最后修改时间，如果长时间未变，说明卡住了
    )
    count = stuck_submissions.count()
    if count > 0:
        for sub in stuck_submissions:
            sub.ai_grading_status = 'failed'
            sub.ai_comment = "AI批改任务超时或系统错误，请联系管理员。"
            sub.save(update_fields=['ai_grading_status', 'ai_comment'])
        logger.info(f"Marked {count} stuck AI grading submissions as failed.")
