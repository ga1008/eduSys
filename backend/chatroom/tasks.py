from celery import shared_task
import logging
from .models import ChatMessage
from utils.minio_tools import MinioClient
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Pillow for thumbnails
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
            'type': 'broadcast_message',
            'message': message_data
        }
    )


@shared_task(name="chatroom.tasks.process_chat_file_upload")
def process_chat_file_upload(message_id, file_content_list, original_name, content_type):
    """
    Celery task to upload a file to Minio and update the chat message.
    """
    message = None
    try:
        message = ChatMessage.objects.select_related('author', 'author__user').get(id=message_id)
        file_content = bytes(file_content_list)

        minio_client = MinioClient()
        file_path = minio_client.upload_file(file_data=file_content)

        # 使用 presigned URL 获取可公开访问的链接
        # 注意：presigned URL有过期时间，如果需要长期有效，需调整MinIO的bucket策略
        public_file_url = minio_client.get_file_url(file_path)

        message.file_path = public_file_url  # 存储可访问的URL
        message.content = f"文件: {original_name}"

        thumbnail_url = None
        if PIL_AVAILABLE and message.message_type == 'image':
            try:
                img = Image.open(BytesIO(file_content))
                # 保持原始宽高比，限制最大尺寸
                img.thumbnail((200, 200))
                thumb_io = BytesIO()
                # 确保保存格式，处理PNG等带透明通道的图片
                img_format = 'PNG' if img.mode in ('RGBA', 'P') else 'JPEG'
                img.save(thumb_io, format=img_format)
                thumb_io.seek(0)
                thumbnail_path_in_minio = minio_client.upload_file(file_data=thumb_io.read())
                thumbnail_url = minio_client.get_file_url(thumbnail_path_in_minio)
                message.thumbnail_path = thumbnail_url  # 存储缩略图URL
            except Exception as e:
                logger.error(f"Failed to generate thumbnail for image {original_name}: {e}")

        message.save()

        # --- 这是最关键的新增部分：广播最终的消息 ---
        # 构造一个与前端期望的完全一致的消息对象
        author_data = None
        if message.author:
            author_data = {
                'id': message.author.id,
                'nickname': message.author.nickname,
                'role': message.author.role,
                'user_id': message.author.user.id,
            }

        final_message_data = {
            'id': message.id,
            'author': author_data,
            'message_type': message.message_type,
            'content': message.content,
            'file_path': message.file_path,
            'file_original_name': message.file_original_name,
            'thumbnail_path': message.thumbnail_path,
            'timestamp': message.timestamp.isoformat(),
            'is_update': True  # 添加一个标志，告诉前端这是对现有消息的更新
        }

        logger.info(f"Broadcasting final message for ID {message.id} to room {message.room.id}")
        broadcast_message_to_room(message.room.id, final_message_data)

    except ChatMessage.DoesNotExist:
        logger.error(f"ChatMessage with id {message_id} does not exist.")
    except Exception as e:
        logger.error(f"Error processing file for message {message_id}: {e}", exc_info=True)
        if message:
            # 如果处理失败，也广播一个失败状态的消息
            message.content = f"文件 {original_name} 上传失败。"
            message.save()
            # 同样构造数据并广播，让前端可以更新UI
            author_data = {'nickname': '系统消息', 'role': 'system'}
            if message.author:
                author_data = {'id': message.author.id, 'nickname': message.author.nickname,
                               'role': message.author.role, 'user_id': message.author.user.id}

            error_message_data = {
                'id': message.id, 'author': author_data, 'message_type': 'system', 'content': message.content,
                'timestamp': message.timestamp.isoformat(), 'is_update': True
            }
            broadcast_message_to_room(message.room.id, error_message_data)
