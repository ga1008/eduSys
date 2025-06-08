# backend/chatroom/tasks.py

from celery import shared_task
import logging
from .models import ChatMessage, ChatRoom
from django.db import models
from utils.minio_tools import MinioClient
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from io import BytesIO

# 用于图片缩略图的Pillow库
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 用于视频缩略图的OpenCV库
try:
    import cv2
    import tempfile
    import os

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


def broadcast_message_to_room(room_id, message_data):
    """一个同步辅助函数，用于从Celery任务内部向Channel Layer广播消息。"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chatroom_{room_id}',
        {
            'type': 'broadcast_message',
            'message': message_data
        }
    )


def get_final_message_data(message, minio_client):
    """构造用于向客户端广播的完整消息负载。"""
    author_data = None
    if message.author:
        author_data = {
            'id': message.author.id,
            'nickname': message.author.nickname,
            'role': message.author.role,
            'user_id': message.author.user.id,
        }

    # 为广播生成预签名URL
    file_url = minio_client.get_file_url(message.file_path) if message.file_path else None
    thumbnail_url = minio_client.get_file_url(message.thumbnail_path) if message.thumbnail_path else None

    return {
        'id': message.id,
        'author': author_data,
        'message_type': message.message_type,
        'content': message.content,
        'file_path': file_url,
        'file_original_name': message.file_original_name,
        'thumbnail_path': thumbnail_url,
        'timestamp': message.timestamp.isoformat(),
        'is_update': True,  # 告知前端替换占位消息的标志
    }


@shared_task(name="chatroom.tasks.process_chat_file_upload")
def process_chat_file_upload(message_id, file_content_list, original_name, content_type):
    """
    Celery任务：上传文件到Minio，如果适用则生成缩略图，并更新相应的聊天消息。
    """
    message = None
    try:
        message = ChatMessage.objects.select_related('author', 'author__user', 'room').get(id=message_id)
        file_content = bytes(file_content_list)

        minio_client = MinioClient()
        # Minio中的对象名是文件内容的哈希值
        object_name = minio_client.upload_file(file_data=file_content)

        # --- 核心修正：存储对象名（哈希），而不是完整的URL ---
        message.file_path = object_name
        message.content = f"文件: {original_name}"

        thumbnail_object_name = None

        # --- 图片缩略图生成 ---
        if PIL_AVAILABLE and message.message_type == 'image':
            try:
                img = Image.open(BytesIO(file_content))
                img.thumbnail((256, 256))
                thumb_io = BytesIO()
                img_format = 'PNG' if img.mode in ('RGBA', 'P') else 'JPEG'
                img.save(thumb_io, format=img_format)
                thumb_io.seek(0)
                thumbnail_object_name = minio_client.upload_file(file_data=thumb_io.read())
            except Exception as e:
                logger.error(f"为图片 {original_name} 生成缩略图失败: {e}")

        # --- 视频缩略图生成 ---
        elif CV2_AVAILABLE and message.message_type == 'video':
            with tempfile.NamedTemporaryFile(delete=False,
                                             suffix=os.path.splitext(original_name)[1]) as temp_video_file:
                temp_video_file.write(file_content)
                temp_video_path = temp_video_file.name

            try:
                cap = cv2.VideoCapture(temp_video_path)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        height, width, _ = frame.shape
                        scale = 256 / max(height, width)
                        new_width, new_height = int(width * scale), int(height * scale)
                        thumbnail = cv2.resize(frame, (new_width, new_height))

                        is_success, buffer = cv2.imencode(".jpg", thumbnail)
                        if is_success:
                            thumbnail_object_name = minio_client.upload_file(file_data=buffer.tobytes())
                cap.release()
            except Exception as e:
                logger.error(f"为视频 {original_name} 生成缩略图失败: {e}")
            finally:
                if os.path.exists(temp_video_path):
                    os.remove(temp_video_path)

        # 存储缩略图的对象名
        if thumbnail_object_name:
            message.thumbnail_path = thumbnail_object_name

        message.save()

        # 向聊天室广播最终的、完整的消息数据
        final_message_data = get_final_message_data(message, minio_client)
        broadcast_message_to_room(message.room.id, final_message_data)
        logger.info(f"成功处理并广播了文件消息: {message.id}")

    except ChatMessage.DoesNotExist:
        logger.error(f"ID为 {message_id} 的聊天消息不存在。")
    except Exception as e:
        logger.error(f"为消息 {message_id} 处理文件时出错: {e}", exc_info=True)
        if message:
            # 向前端广播一个错误更新
            error_message_data = {
                'id': message.id, 'message_type': 'system', 'content': f"文件 {original_name} 上传失败。",
                'timestamp': timezone.now().isoformat(), 'is_update': True,
                'author': {'nickname': '系统', 'role': 'system'},
            }
            broadcast_message_to_room(message.room.id, error_message_data)


@shared_task(name="chatroom.tasks.cleanup_expired_files")
def cleanup_expired_files():
    """
    一个每日任务，用于查找并从MinIO中删除超过7天的聊天文件。
    """
    logger.info("开始每日清理过期的聊天文件...")
    expiration_date = timezone.now() - timedelta(days=7)

    expired_messages = ChatMessage.objects.filter(
        models.Q(message_type__in=['image', 'video', 'file']),
        timestamp__lt=expiration_date,
        file_path__isnull=False
    )

    if not expired_messages.exists():
        logger.info("没有需要清理的过期文件。")
        return

    minio_client = MinioClient()
    deleted_count = 0

    for message in expired_messages:
        if message.file_path:
            minio_client.delete_file(message.file_path)
            deleted_count += 1

        if message.thumbnail_path:
            minio_client.delete_file(message.thumbnail_path)

        message.file_path = None
        message.thumbnail_path = None
        message.content = f"[文件 '{message.file_original_name}' 已过期并被自动删除]"
        message.save(update_fields=['file_path', 'thumbnail_path', 'content'])

    logger.info(f"清理完成。从MinIO中删除了 {deleted_count} 个过期文件。")
