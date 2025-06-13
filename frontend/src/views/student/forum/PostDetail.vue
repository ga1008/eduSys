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

      <div class="post-content" v-html="purifiedContent"></div>
      <!-- 这里可以添加显示帖子文件的逻辑 -->
      <div class="post-attachments" v-if="post.files && post.files.length > 0">
        <h4>附件：</h4>
        <div v-for="file in post.files" :key="file.id" class="attachment-item">
          <el-image
              v-if="file.file_type === 'IMAGE' || file.file_type === 'GIF'"
              :src="file.thumbnail_url || file.file_url"
              :preview-src-list="[file.file_url]"
              fit="cover"
              class="attachment-thumbnail"
          />
          <div v-else-if="file.file_type === 'VIDEO'" class="video-thumbnail" @click="playVideo(file.file_url)">
            <el-image :src="file.thumbnail_url" fit="cover"/>
            <el-icon class="play-icon">
              <VideoPlay/>
            </el-icon>
          </div>
          <el-link v-else :href="file.file_url" target="_blank">{{ file.original_name }}</el-link>
        </div>
      </div>

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
      <div v-if="post && post.comments">
        <div v-if="pinnedComments.length > 0" class="pinned-comments">
          <div class="pinned-header">热门评论</div>
          <div v-for="(comment, index) in pinnedComments" :key="comment.id" class="comment-item">
            <span class="floor-number">#{{ getFloorNumber(comment) }}</span>
            <el-button text :icon="comment.is_liked ? StarFilled : Star" @click="toggleCommentLike(comment)">
              {{ comment.like_count }}
            </el-button>
          </div>
        </div>

        <el-divider v-if="pinnedComments.length > 0 && regularComments.length > 0"/>

        <div v-for="(comment, index) in regularComments" :key="comment.id" class="comment-item">
          <span class="floor-number">#{{ getFloorNumber(comment) }}</span>
          <div v-if="comment.parent_comment" class="reply-to">
            回复 #{{ getFloorNumber(findCommentById(comment.parent_comment)) }}
          </div>
          <el-button text :icon="comment.is_liked ? StarFilled : Star" @click="toggleCommentLike(comment)">
            {{ comment.like_count }}
          </el-button>
        </div>
      </div>

    </el-card>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {createComment, fetchPostById, likePost, unlikePost} from '@/api/forum';
import {Pointer, Star, StarFilled} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import DOMPurify from 'dompurify';
import MarkdownIt from 'markdown-it';
import {likeComment, unlikeComment} from '@/api/forum'; // 需要在api/forum.js中新增


const md = new MarkdownIt();
const allComments = computed(() => post.value?.comments || []);

const pinnedComments = computed(() => {
  // 假设后端已按点赞排序，取前3个且点赞数>0的
  return allComments.value.slice(0, 3).filter(c => c.like_count > 0);
});

const regularComments = computed(() => {
  const pinnedIds = new Set(pinnedComments.value.map(c => c.id));
  return allComments.value.filter(c => !pinnedIds.has(c.id));
});

const getFloorNumber = (comment) => {
  const index = allComments.value.findIndex(c => c.id === comment.id);
  return index + 1;
};

const findCommentById = (id) => {
  return allComments.value.find(c => c.id === id);
};

const toggleCommentLike = async (comment) => {
  try {
    const apiCall = comment.is_liked ? unlikeComment : likeComment;
    const response = await apiCall(postId, comment.id); // API需要支持
    comment.is_liked = !comment.is_liked;
    comment.like_count = response.data.like_count;
  } catch (e) {
    ElMessage.error("点赞失败");
  }
}

const purifiedContent = computed(() => {
  if (post.value && post.value.content) {
    const rawHtml = md.render(post.value.content);
    return DOMPurify.sanitize(rawHtml);
  }
  return '';
});

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
