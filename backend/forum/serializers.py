# backend/forum/serializers.py

from rest_framework import serializers

from utils.minio_tools import MinioClient
from .models import Tag, Post, PostFile, Comment, PostLike
from education.serializers import UserSimpleSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class PostFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = PostFile
        fields = ['id', 'original_name', 'file_type', 'file_url', 'thumbnail_url']

    def get_file_url(self, obj):
        # 生成带签名的访问URL
        if obj.file_path:
            client = MinioClient()
            return client.get_file_url(obj.file_path)
        return None

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_path:
            client = MinioClient()
            return client.get_file_url(obj.thumbnail_path)
        return self.get_file_url(obj)  # 如果没缩略图，返回原图URL


class CommentAuthorSerializer(UserSimpleSerializer):
    """用于评论中显示作者信息的序列化器，处理匿名"""
    class_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta(UserSimpleSerializer.Meta):
        fields = ['id', 'username', 'name', 'real_name', 'avatar', 'role', 'class_name', 'avatar_url']

    def get_class_name(self, obj):
        # 返回班级名称，如果没有班级则返回空字符串
        return obj.class_enrolled.name if obj.class_enrolled else ''

    def get_avatar_url(self, obj):
        # 返回头像的完整URL
        if obj.avatar:
            client = MinioClient()
            return client.get_file_url(obj.avatar)
        return None


class ReplySerializer(serializers.ModelSerializer):
    """用于嵌套显示的回复序列化器"""
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'is_anonymous', 'is_ai_generated', 'created_at']

    def get_author(self, obj):
        if obj.is_anonymous and not obj.is_ai_generated:
            return {'id': None, 'username': '匿名用户', 'real_name': '匿名用户', 'avatar': None}
        if obj.is_ai_generated:
            return {'id': 'ai', 'username': 'AI 助教', 'real_name': 'AI 助教', 'avatar': None}  # 前端可根据 id='ai' 显示特定头像
        return CommentAuthorSerializer(obj.author).data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = ReplySerializer(many=True, read_only=True)
    is_liked = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'is_anonymous', 'is_ai_generated', 'parent_comment', 'created_at',
                  'replies',
                  'like_count', 'is_liked',
                  ]
        extra_kwargs = {
            'parent_comment': {'write_only': True}
        }

    def get_author(self, obj):
        if obj.is_anonymous and not obj.is_ai_generated:
            return {'id': None, 'username': '匿名用户', 'real_name': '匿名用户', 'avatar': None}
        if obj.is_ai_generated:
            return {'id': 'ai', 'username': 'AI 助教', 'real_name': 'AI 助教', 'avatar': None}
        return CommentAuthorSerializer(obj.author).data


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    files = PostFileSerializer(many=True, read_only=True)  # 修改：使用新的序列化器
    comments = CommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    views = serializers.IntegerField(source='view_count', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author', 'tags', 'files', 'comments',
            'is_anonymous', 'visibility', 'allow_comments', 'allow_ai_comments',
            'view_count', 'like_count', 'comment_count', 'is_liked',
            'created_at', 'updated_at', 'files', 'views'
        ]

    def get_views(self, obj):
        return obj.view_count

    def get_author(self, obj):
        user = self.context['request'].user
        # 规则：1. 作者自己可见 2. 超管可见 3. 老师对其学生可见
        can_view_real_name = (
                user.is_superuser or
                obj.author == user or
                (user.role == 'teacher' and obj.author.role == 'student' and
                 obj.author.class_enrolled in user.teacher_classes.all())
        )

        if obj.is_anonymous and not can_view_real_name:
            return {'id': None, 'username': '匿名用户', 'real_name': '匿名用户', 'avatar': None}
        client = MinioClient()
        avatar_url = client.get_file_url(obj.author.avatar) if obj.author.avatar else None
        data = {
            'id': obj.author.id,
            'username': obj.author.username,
            'real_name': obj.author.name if can_view_real_name else '匿名用户',
            'name': obj.author.name if can_view_real_name else '匿名用户',
            'avatar': avatar_url,
            'role': obj.author.role,
            'class_name': obj.author.class_enrolled.name if obj.author.class_enrolled else ''
        }
        return data

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=user).exists()
        return False

    def validate(self, data):
        # 规则：老师和超管不能匿名发帖
        user = self.context['request'].user
        if user.role in ['teacher', 'admin'] and data.get('is_anonymous', False):
            raise serializers.ValidationError("教师和管理员不允许匿名发帖。")
        return data
