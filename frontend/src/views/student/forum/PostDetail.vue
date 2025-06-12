<template>
  <div class="post-detail-page" v-loading="loading">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="text-large font-600 mr-3">帖子详情</span>
      </template>
    </el-page-header>

    <el-card v-if="post" class="post-card">
      <template #header>
        <h1 class="post-title">{{ post.title }}</h1>
        <div class="author-meta">
          <el-avatar :size="40" :src="post.author.avatar || defaultAvatar"/>
          <div class="author-info">
            <span class="author-name">{{ post.author.real_name || '匿名用户' }}</span>
            <span class="post-time">{{ formatTime(post.created_at) }}</span>
          </div>
          <div class="post-actions">
            <el-button :type="post.is_liked ? 'primary' : ''" :icon="StarFilled"
                       @click="toggleLike" round>
              {{ post.like_count }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="post-content" v-html="post.content"></div>
      <!-- 这里可以添加显示帖子文件的逻辑 -->

    </el-card>

    <!-- 评论区 -->
    <el-card class="comments-section">
      <template #header>
        <div class="card-header">
          <span>{{ post?.comment_count || 0 }} 条评论</span>
        </div>
      </template>

      <!-- 发表评论 -->
      <div class="comment-composer">
        <el-input
            v-model="newComment.content"
            type="textarea"
            :rows="3"
            placeholder="发表你的看法..."
        />
        <div class="composer-actions">
          <el-switch v-model="newComment.is_anonymous" active-text="匿名评论"/>
          <el-button type="primary" @click="submitComment" :loading="submittingComment">发表评论</el-button>
        </div>
      </div>

      <!-- 评论列表 -->
      <div v-for="comment in post?.comments" :key="comment.id" class="comment-item">
        <el-avatar :size="32" :src="comment.author.avatar || defaultAvatar"/>
        <div class="comment-body">
          <div class="comment-header">
            <span class="comment-author">{{ comment.author.real_name || '匿名用户' }}</span>
            <el-tag v-if="comment.is_ai_generated" type="primary" size="small" effect="dark">AI助教</el-tag>
          </div>
          <div class="comment-content">{{ comment.content }}</div>
          <div class="comment-footer">
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
            <!-- 回复功能可以后续添加 -->
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {createComment, fetchPostById, likePost, unlikePost} from '@/api/forum';
import {Pointer, Star, StarFilled} from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();

const postId = route.params.postId;
const post = ref(null);
const loading = ref(true);
const submittingComment = ref(false);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const newComment = ref({
  content: '',
  is_anonymous: true,
});

const loadPost = async () => {
  loading.value = true;
  try {
    const res = await fetchPostById(postId);
    post.value = res.data;
  } catch (error) {
    ElMessage.error('加载帖子失败');
    router.back();
  } finally {
    loading.value = false;
  }
};

const goBack = () => router.back();

const formatTime = (time) => dayjs(time).fromNow();

const toggleLike = async () => {
  if (!post.value) return;
  try {
    if (post.value.is_liked) {
      await unlikePost(postId);
      post.value.like_count--;
    } else {
      await likePost(postId);
      post.value.like_count++;
    }
    post.value.is_liked = !post.value.is_liked;
  } catch (error) {
    ElMessage.error('操作失败');
  }
};

const submitComment = async () => {
  if (!newComment.value.content.trim()) {
    ElMessage.warning('评论内容不能为空');
    return;
  }
  submittingComment.value = true;
  try {
    await createComment(postId, newComment.value);
    ElMessage.success('评论成功！');
    newComment.value.content = '';
    loadPost(); // 重新加载帖子数据以显示新评论
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '评论失败');
  } finally {
    submittingComment.value = false;
  }
}

onMounted(loadPost);
</script>

<style scoped>
.post-detail-page {
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.post-card, .comments-section {
  margin-bottom: 20px;
}

.post-title {
  font-size: 1.8rem;
  margin-bottom: 20px;
}

.author-meta {
  display: flex;
  align-items: center;
}

.author-info {
  margin-left: 12px;
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 500;
}

.post-time {
  font-size: 0.8rem;
  color: #8590a6;
}

.post-actions {
  margin-left: auto;
}

.post-content {
  line-height: 1.8;
  padding: 20px 0;
  font-size: 1rem;
}

.comment-composer {
  margin-bottom: 30px;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.comment-item {
  display: flex;
  padding: 15px 0;
  border-top: 1px solid #f0f2f5;
}

.comment-body {
  margin-left: 12px;
  width: 100%;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.comment-author {
  font-weight: 500;
  font-size: 0.95rem;
}

.comment-content {
  line-height: 1.7;
  color: #1a1a1a;
}

.comment-footer {
  margin-top: 8px;
  font-size: 0.8rem;
  color: #8590a6;
}
</style>
