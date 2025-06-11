# backend/forum/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import F, Q, Count
from datetime import timedelta
from django.utils import timezone

from .models import Post, Comment, Tag, PostVisibilityRule
from .serializers import PostSerializer, CommentSerializer, TagSerializer
from .permissions import CanManageForumContent
from .tasks import trigger_ai_comment


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, CanManageForumContent]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tags__name']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'like_count', 'comment_count', 'view_count']

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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related('author').prefetch_related('replies')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, CanManageForumContent]

    def get_queryset(self):
        # 确保只返回特定帖子下的评论
        return self.queryset.filter(post_id=self.kwargs['post_pk'])

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)
        # 更新帖子评论数
        post.comment_count = F('comment_count') + 1
        post.save(update_fields=['comment_count'])


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """用于浏览和搜索标签的视图"""
    queryset = Tag.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
