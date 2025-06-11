# backend/forum/models.py

from django.db import models
from education.models import User


class Tag(models.Model):
    """帖子标签"""
    name = models.CharField(max_length=50, unique=True, verbose_name="标签名称")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "帖子标签"
        verbose_name_plural = verbose_name


class Post(models.Model):
    """校园帖子"""
    VISIBILITY_CHOICES = [
        ('PUBLIC', '公开'),
        ('PRIVATE', '部分可见'),  # 通过白名单/黑名单控制
    ]

    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts', verbose_name="作者")
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name="标签")

    is_anonymous = models.BooleanField(default=True, verbose_name="是否匿名")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PUBLIC', verbose_name="可见范围")

    allow_comments = models.BooleanField(default=True, verbose_name="允许评论")
    allow_ai_comments = models.BooleanField(default=False, verbose_name="允许AI跟评")

    # 用于热帖排行
    view_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    like_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    comment_count = models.PositiveIntegerField(default=0, verbose_name="评论数")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "帖子"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class PostFile(models.Model):
    """帖子附件，支持图片、视频、文件"""
    FILE_TYPE_CHOICES = [
        ('IMAGE', '图片'),
        ('VIDEO', '视频'),
        ('FILE', '文件'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='files')
    file_path = models.CharField(max_length=255, verbose_name="文件路径 (MinIO)")
    original_name = models.CharField(max_length=255, verbose_name="原始文件名")
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, verbose_name="文件类型")
    thumbnail_path = models.CharField(max_length=255, blank=True, null=True, verbose_name="缩略图路径")

    def __str__(self):
        return self.original_name


class Comment(models.Model):
    """帖子评论"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="所属帖子")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments', verbose_name="评论者")
    content = models.TextField(verbose_name="评论内容")

    # 支持多级评论
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    is_anonymous = models.BooleanField(default=True, verbose_name="是否匿名")
    is_ai_generated = models.BooleanField(default=False, verbose_name="是否为AI生成")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author} on {self.post.title}'

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = verbose_name
        ordering = ['created_at']


class PostLike(models.Model):
    """帖子点赞记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # 每人只能点赞一次


class PostVisibilityRule(models.Model):
    """帖子可见性规则（黑名单/白名单）"""
    RULE_CHOICES = [
        ('ALLOW', '允许（白名单）'),
        ('DENY', '禁止（黑名单/拉黑）'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='visibility_rules')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rule_type = models.CharField(max_length=5, choices=RULE_CHOICES)

    class Meta:
        unique_together = ('post', 'user')
