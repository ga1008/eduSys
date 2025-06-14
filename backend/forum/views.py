# backend/forum/views.py
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import F, Q, Count, OuterRef, Exists, Sum, IntegerField
from datetime import timedelta
from django.utils import timezone

from .models import Post, Comment, Tag, PostVisibilityRule, CommentLike
from .serializers import PostSerializer, CommentSerializer, TagSerializer
from .permissions import CanManageForumContent
from .tasks import trigger_ai_comment, process_forum_file_upload


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, CanManageForumContent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tags__name']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'like_count', 'comment_count', 'view_count']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user

        # 过滤掉被黑名单的用户帖子
        blocked_user_ids = PostVisibilityRule.objects.filter(
            user=user, rule_type='DENY'
        ).values_list('post__author_id', flat=True)

        # 过滤掉私有且用户不在白名单的帖子
        private_posts_allowed = PostVisibilityRule.objects.filter(
            user=user, rule_type='ALLOW'
        ).values_list('post_id', flat=True)

        queryset = Post.objects.exclude(
            author_id__in=blocked_user_ids
        ).filter(
            Q(visibility='PUBLIC') |
            (Q(visibility='PRIVATE') & Q(id__in=private_posts_allowed)) |
            Q(author=user)  # 总是能看到自己的帖子
        ).distinct().prefetch_related(
            'tags', 'files', 'likes'
        ).select_related('author')

        return queryset

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)

        # 处理上传的文件
        files = self.request.FILES.getlist('files')
        for file_obj in files:
            # 将文件处理移交Celery异步执行
            process_forum_file_upload.delay(
                post.id,
                list(file_obj.read()),  # 文件内容转为列表以被json序列化
                file_obj.name,
                file_obj.content_type
            )

        if post.allow_ai_comments:
            trigger_ai_comment.delay(post.id)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = post.likes.get_or_create(user=request.user)
        if created:
            post.like_count = F('like_count') + 1
            post.save(update_fields=['like_count'])
        return Response({'status': 'liked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        post = self.get_object()
        deleted_count, _ = post.likes.filter(user=request.user).delete()
        if deleted_count > 0:
            post.like_count = F('like_count') - 1
            post.save(update_fields=['like_count'])
        return Response({'status': 'unliked'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """获取热点帖子，例如过去7天内按点赞和评论数排序"""
        period = request.query_params.get('period', 'week')  # 'week' or 'month'
        days = 30 if period == 'month' else 7

        since = timezone.now() - timedelta(days=days)

        hot_posts = self.get_queryset().filter(created_at__gte=since).annotate(
            hotness=F('like_count') + F('comment_count') * 2  # 简单加权
        ).order_by('-hotness', '-created_at')[:10]  # 取前10条

        serializer = self.get_serializer(hot_posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def hot(self, request):
        period = request.query_params.get('period', 'week')
        days = 30 if period == 'month' else 7
        since = timezone.now() - timedelta(days=days)

        hot_posts = self.get_queryset().filter(created_at__gte=since).annotate(
            # Coalesce(Sum(...), 0) 防止没有评论时Sum返回NULL导致错误
            total_likes=F('like_count') + Coalesce(Sum('comments__like_count'), 0, output_field=IntegerField()),
            hotness=F('total_likes') + F('comment_count') * 2
        ).order_by('-hotness', '-created_at')[:10]

        serializer = self.get_serializer(hot_posts, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related('author').prefetch_related('replies')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CanManageForumContent]

    def get_queryset(self):
        post_pk = self.kwargs['post_pk']
        user = self.request.user

        # 标记用户是否点赞
        user_likes = CommentLike.objects.filter(
            comment=OuterRef('pk'),
            user=user
        )

        # 1. 获取该帖子的所有一级评论 (parent_comment is NULL)
        base_queryset = Comment.objects.filter(
            post_id=post_pk,
            parent_comment__isnull=True
        ).annotate(
            is_liked=Exists(user_likes)
        )

        # 2. 按点赞数倒序，创建时间正序排序
        return base_queryset.order_by('-like_count', 'created_at')

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)
        # 更新帖子评论数
        post.comment_count = F('comment_count') + 1
        post.save(update_fields=['comment_count'])

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, post_pk=None, pk=None):
        comment = self.get_object()
        _, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if created:
            comment.like_count = F('like_count') + 1
            comment.save(update_fields=['like_count'])

        # ✨ 新增：从数据库刷新 comment 对象
        comment.refresh_from_db()

        # ✨ 修改：返回完整的点赞数和点赞状态
        return Response({
            'status': 'liked',
            'like_count': comment.like_count,
            'is_liked': True  # 点赞后状态必然为 True
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, post_pk=None, pk=None):
        comment = self.get_object()
        deleted_count, _ = CommentLike.objects.filter(user=request.user, comment=comment).delete()
        if deleted_count > 0:
            comment.like_count = F('like_count') - 1
            comment.save(update_fields=['like_count'])

        # ✨ 新增：从数据库刷新 comment 对象
        comment.refresh_from_db()

        # ✨ 修改：返回正确的点赞数和点赞状态
        return Response({
            'status': 'unliked',
            'like_count': comment.like_count,
            'is_liked': False  # 取消点赞后状态必然为 False
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        # 检查父评论是否存在于同一个帖子下
        parent_comment_id = self.request.data.get('parent_comment')
        if parent_comment_id:
            parent_comment = Comment.objects.filter(id=parent_comment_id, post=post).first()
            if not parent_comment:
                raise serializers.ValidationError("回复的评论不存在或不属于当前帖子。")

        comment = serializer.save(author=self.request.user, post=post)
        post.comment_count = F('comment_count') + 1
        post.save(update_fields=['comment_count'])


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """用于浏览和搜索标签的视图"""
    queryset = Tag.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
