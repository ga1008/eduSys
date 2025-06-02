from io import BytesIO

from django.conf import settings
from minio import Minio


class MinioClient:
    def __init__(self):
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_USER,
            secret_key=settings.MINIO_ACCESS_KEY,
            secure=getattr(settings, "MINIO_USE_SSL", False)
        )
        self.bucket_name = settings.MINIO_BUCKET
        self.create_bucket_if_not_exists()

    def create_bucket_if_not_exists(self):
        """创建存储桶，如果不存在的话"""
        if not self.minio_client.bucket_exists(self.bucket_name):
            self.minio_client.make_bucket(self.bucket_name)
            print(f"Bucket '{self.bucket_name}' created.")
        else:
            print(f"Bucket '{self.bucket_name}' already exists.")

    def file_hash_md5(self, file_data):
        """计算文件的MD5哈希值"""
        import hashlib
        hash_md5 = hashlib.md5()
        hash_md5.update(file_data)
        return hash_md5.hexdigest()

    def is_exist(self, file_data):
        """检查对象是否存在"""
        object_name = self.file_hash_md5(file_data)
        try:
            self.minio_client.stat_object(self.bucket_name, object_name)
            return True
        except Exception as e:
            return False

    def is_exist_name(self, object_name):
        """检查对象是否存在"""
        try:
            self.minio_client.stat_object(self.bucket_name, object_name)
            return True
        except Exception as e:
            return False

    def upload_file(self, file_data):
        """上传文件到MinIO"""
        object_name = self.file_hash_md5(file_data)
        if not self.is_exist_name(object_name):
            file_io = BytesIO(file_data)
            self.minio_client.put_object(
                self.bucket_name,
                object_name,
                file_io,
                len(file_data)
            )
            print(f"文件 '{object_name}' 已上传")
        else:
            print(f"文件 '{object_name}' 已存在")
        return object_name

    def download_file(self, object_name):
        """返回二进制文件"""
        try:
            response = self.minio_client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            print(f"下载文件 '{object_name}' 失败: {e}")
            return None

    def delete_file(self, object_name):
        """删除文件"""
        if self.is_exist_name(object_name):
            try:
                self.minio_client.remove_object(self.bucket_name, object_name)
                print(f"文件 '{object_name}' 已删除")
                return True
            except Exception as e:
                print(f"删除文件 '{object_name}' 失败: {e}")

    def list_files(self):
        """列出存储桶中的所有文件"""
        objects = self.minio_client.list_objects(self.bucket_name)
        files = []
        for obj in objects:
            files.append(obj.object_name)
        return files

    def get_file_url(self, object_name):
        """获取文件的URL"""
        try:
            url = self.minio_client.presigned_get_object(self.bucket_name, object_name)
            return url
        except Exception as e:
            print(f"获取文件 '{object_name}' 的URL失败: {e}")
            return None

    def get_file_info(self, object_name):
        """获取文件信息"""
        try:
            stat = self.minio_client.stat_object(self.bucket_name, object_name)
            return {
                "name": stat.object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag
            }
        except Exception as e:
            print(f"获取文件 '{object_name}' 的信息失败: {e}")
            return None
