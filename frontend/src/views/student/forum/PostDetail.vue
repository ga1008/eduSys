<template>
  <div class="post-detail-page" v-loading="loading">
    <el-page-header @back="router.back()" class="page-header">
      <template #content>
        <span class="text-large font-600">帖子详情</span>
      </template>
    </el-page-header>

    <el-card
        v-if="post"
        class="post-card"
        :class="{'reply-highlight': activeReply.type === 'post'}"
        :body-style="{padding: '20px'}"
    >
      <template #header>
        <div class="post-header-content">
          <h1 class="post-title">{{ post.title }}</h1>
          <div class="author-meta">
            <el-avatar :size="40" :src="post.author.avatar || defaultAvatar"/>
            <div class="author-info">
              <span class="author-name">{{ getAuthorName(post.author) }}</span>
              <div class="meta-tags">
                <el-tag type="info" size="small">{{ formatTime(post.created_at) }}</el-tag>
                <el-tag type="info" size="small">围观 {{ post.view_count }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div class="post-content markdown-body" v-html="purifiedContent"></div>

      <div class="post-footer-actions">
        <el-button :type="post.is_liked ? 'primary' : 'default'" :icon="CaretTop" round @click="handleTogglePostLike">
          {{ post.like_count }} 赞
        </el-button>
        <el-button :icon="ChatDotRound" round @click="toggleReply('post')">
          {{ post.comment_count }} 评论
        </el-button>
      </div>

      <transition name="fade-slide">
        <div v-if="activeReply.type === 'post'" class="comment-composer-wrapper" ref="postComposerRef">
          <CommentComposer
              placeholder="发表你的看法..."
              :is-submitting="submitting"
              @submit="submitComment"
              @cancel="cancelReply"
          />
        </div>
      </transition>
    </el-card>

    <el-skeleton v-else :rows="6" animated/>

    <el-card class="comments-section" v-if="post">
      <div v-if="hotComments.length > 0" class="hot-comments-area">
        <h3 class="area-title">热门评论</h3>
        <div class="comments-list">
          <CommentNode
              v-for="item in hotComments"
              :key="`hot-${item.id}`"
              :comment="item"
              :active-reply="activeReply"
              :is-submitting="submitting"
              :register-ref="registerCommentRef"
              class="top-level-comment"
              @reply="toggleReply('comment', $event)"
              @submit="submitComment"
              @cancel="cancelReply"
              @like="handleToggleCommentLike"
          />
        </div>
      </div>

      <el-divider v-if="hotComments.length > 0 && sortedComments.length > 0">
        <span class="divider-text">最新评论</span>
      </el-divider>

      <div v-if="post.comments && post.comments.length > 0" class="latest-comments-area">
        <h3 class="area-title" v-if="hotComments.length === 0">全部评论 ({{ post.comment_count }})</h3>
        <div class="comments-list">
          <CommentNode
              v-for="item in sortedComments"
              :key="item.id"
              :comment="item"
              :active-reply="activeReply"
              :is-submitting="submitting"
              :register-ref="registerCommentRef"
              class="top-level-comment"
              @reply="toggleReply('comment', $event)"
              @submit="submitComment"
              @cancel="cancelReply"
              @like="handleToggleCommentLike"
          />
        </div>
      </div>
      <el-empty v-else description="还没有评论，快来发表你的看法吧！"/>
    </el-card>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted, nextTick} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {fetchPostById, createComment, likePost, unlikePost, likeComment, unlikeComment, viewPost} from '@/api/forum';
import {ElMessage} from 'element-plus';
import {CaretTop, ChatDotRound} from '@element-plus/icons-vue';

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

import DOMPurify from 'dompurify';
import MarkdownIt from 'markdown-it';

import CommentComposer from './CommentComposer.vue';
import CommentNode from './CommentNode.vue';

// --- 初始化 ---
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const route = useRoute();
const router = useRouter();
const postId = route.params.postId;

const md = new MarkdownIt();
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

// --- 响应式状态 ---
const loading = ref(true);
const submitting = ref(false);
const post = ref(null);
const activeReply = reactive({type: null, id: null});
const commentRefs = new Map();
const postComposerRef = ref(null);

// --- 计算属性 ---
const purifiedContent = computed(() =>
    post.value?.content ? DOMPurify.sanitize(md.render(post.value.content)) : ''
);

// 新增：计算热门评论
const hotComments = computed(() => {
  if (!post.value?.comments) return [];
  return [...post.value.comments]
      .map(comment => ({
        ...comment,
        hotness: comment.like_count + (comment.replies?.length || 0)
      }))
      .filter(comment => comment.hotness > 0)
      .sort((a, b) => b.hotness - a.hotness)
      .slice(0, 3);
});

// 新增：计算常规排序的评论（排除热门）
const sortedComments = computed(() => {
  if (!post.value?.comments) return [];
  const hotCommentIds = new Set(hotComments.value.map(c => c.id));
  return post.value.comments.filter(comment => !hotCommentIds.has(comment.id));
});

// --- 帮助函数 ---
const getAuthorName = (author) =>
    author?.class_name ? `${author.class_name} ${author.name}` : author?.name || '匿名用户';
const formatTime = (time) => dayjs(time).fromNow();
const registerCommentRef = (id, el) => {
  if (id && el) commentRefs.set(id, el);
};

// --- API & 交互逻辑 ---
const loadPost = async () => {
  loading.value = true;
  try {
    const res = await fetchPostById(postId);
    post.value = res.data;
  } catch (err) {
    ElMessage.error('帖子加载失败');
    router.back();
  } finally {
    loading.value = false;
  }
};

const submitComment = async (content) => {
  if (submitting.value) return;
  submitting.value = true;
  try {
    await createComment(postId, {
      content,
      is_anonymous: false,
      parent_comment: activeReply.type === 'comment' ? activeReply.id : null,
    });
    ElMessage.success('发布成功');
    cancelReply();
    await loadPost();
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发布失败');
  } finally {
    submitting.value = false;
  }
};

const handleTogglePostLike = async () => { /* ... (代码无变化) ... */
};

// 新增：处理评论点赞
const handleToggleCommentLike = async (comment) => {
  // 找到原始评论对象以确保响应性
  const findComment = (list, id) => {
    for (const c of list) {
      if (c.id === id) return c;
      if (c.replies) {
        const found = findComment(c.replies, id);
        if (found) return found;
      }
    }
    return null;
  };
  const targetComment = findComment(post.value.comments, comment.id);
  if (!targetComment) return;

  try {
    if (targetComment.is_liked) {
      await unlikeComment(targetComment.id);
      targetComment.is_liked = false;
      targetComment.like_count--;
    } else {
      await likeComment(targetComment.id);
      targetComment.is_liked = true;
      targetComment.like_count++;
    }
  } catch {
    ElMessage.error('操作失败');
  }
};

const toggleReply = async (type, id = null) => {
  if (activeReply.type === type && activeReply.id === id) {
    cancelReply();
    return;
  }
  activeReply.type = type;
  activeReply.id = id;

  await nextTick();
  const targetRef = type === 'post' ? postComposerRef.value : commentRefs.get(id);
  targetRef?.scrollIntoView({behavior: 'smooth', block: 'center'});
};

const cancelReply = () => {
  activeReply.type = null;
  activeReply.id = null;
};

onMounted(async () => {
  await loadPost();
  if (postId) {
    try {
      await viewPost(postId);
    } catch (e) {
      console.error('Failed to record view count:', e);
    }
  }
});
</script>

<style scoped>
.post-detail-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.post-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.post-header-content .post-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

.author-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.author-name {
  font-weight: 500;
}

.meta-tags {
  display: flex;
  gap: 8px;
}

.post-content {
  margin-top: 20px;
  font-size: 16px;
  line-height: 1.7;
}

.post-footer-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f2f5;
}

/* === 评论区整体样式 === */
.comments-section {
  margin-top: 20px;
  border-radius: 8px;
}

.area-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.divider-text {
  color: #888;
  font-weight: 400;
}

/* === 新增：为顶级评论添加分割线 === */
.top-level-comment {
  border-bottom: 1px solid #f0f2f5;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.top-level-comment:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.reply-highlight {
  background-color: #f0f8ff;
  border-color: #a0cfff;
}

.comment-composer-wrapper {
  margin-top: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.25s ease-out;
}

.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>