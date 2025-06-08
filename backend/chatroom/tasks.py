# backend/chatroom/tasks.py

from celery import shared_task
import logging
from .models import ChatMessage, ChatRoom
from utils.minio_tools import MinioClient
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import mimetypes

# Pillow for thumbnails, moviepy for video thumbnails (optional)
try:
    from PIL import Image
    from io import BytesIO

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


def broadcast_message_to_room(room_id, message_data):
    """同步函数，用于从Celery任务中向Channel Layer发送消息"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chatroom_{room_id}',
        {
            'type': 'broadcast_message',  # Corresponds to the method in ChatConsumer
            'message': message_data
        }
    )


@shared_task(name="chatroom.tasks.process_chat_file_upload")
def process_chat_file_upload(message_id, file_content_list, original_name, content_type):
    """
    Celery task to upload a file to Minio and update the chat message.
    """
    try:
        message = ChatMessage.objects.get(id=message_id)
        file_content = bytes(file_content_list)

        minio_client = MinioClient()
        file_path = minio_client.upload_file(file_data=file_content)

        message.file_path = file_path
        message.content = f"文件: {original_name}"  # 更新占位符内容

        # --- 缩略图生成逻辑 ---
        thumbnail_path = None
        if PIL_AVAILABLE and message.message_type == 'image':
            try:
                img = Image.open(BytesIO(file_content))
                img.thumbnail((200, 200))  # 创建最大200x200的缩略图
                thumb_io = BytesIO()
                img_format = img.format or 'JPEG'
                img.save(thumb_io, format=img_format)
                thumb_io.seek(0)
                thumbnail_path = minio_client.upload_file(file_data=thumb_io.read())
                message.thumbnail_path = thumbnail_path
            except Exception as e:
                logger.error(f"Failed to generate thumbnail for image {original_name}: {e}")

        # (可选) 视频缩略图生成可以使用 moviepy，比较消耗资源
        # if message.message_type == 'video': ...

        message.save()

        # 任务完成后，广播最终的消息给聊天室
        from .serializers import ChatMessageSerializer
        final_message_data = ChatMessageSerializer(message).data
        broadcast_message_to_room(message.room.id, final_message_data)

    except ChatMessage.DoesNotExist:
        logger.error(f"ChatMessage with id {message_id} does not exist.")
    except Exception as e:
        logger.error(f"Error processing file for message {message_id}: {e}")
        # (可选) 更新消息状态为“上传失败”并广播
        message.content = f"文件 {original_name} 上传失败。"
        message.save()
        # broadcast_message_to_room(...)


@shared_task(name="chatroom.tasks.cleanup_expired_files")
def cleanup_expired_files():
    """
    清理超过7天的文件。
    """
    seven_days_ago = timezone.now() - timedelta(days=7)
    expired_messages = ChatMessage.objects.filter(
        message_type__in=['file', 'image', 'video'],
        timestamp__lt=seven_days_ago,
        file_path__isnull=False
    )
    minio_client = MinioClient()
    for msg in expired_messages:
        if msg.file_path:
            minio_client.delete_file(msg.file_path)
        if msg.thumbnail_path:
            minio_client.delete_file(msg.thumbnail_path)
    logger.info(f"Cleaned up {expired_messages.count()} expired chat files.")


@shared_task(name="chatroom.tasks.cleanup_expired_messages")
def cleanup_expired_messages():
    """
    清理超过1个月的聊天记录。
    """
    one_month_ago = timezone.now() - timedelta(days=30)
    count, _ = ChatMessage.objects.filter(timestamp__lt=one_month_ago).delete()
    logger.info(f"Deleted {count} chat messages older than one month.")
