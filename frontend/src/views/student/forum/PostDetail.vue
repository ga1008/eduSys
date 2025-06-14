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
            <el-button :type="post.is_liked ? 'primary' : 'default'" :icon="StarFilled" @click="togglePostLike" round>
              点赞 {{ post.like_count }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="post-content markdown-body" v-html="purifiedContent"></div>

      <div class="post-attachments" v-if="post.files && post.files.length > 0">
        <el-divider>附件</el-divider>
        <div class="attachment-grid">
          <div v-for="file in post.files" :key="file.id" class="attachment-item">
            <el-image
                v-if="file.file_type === 'IMAGE' || file.file_type === 'GIF'"
                :src="file.thumbnail_url || file.file_url"
                :preview-src-list="[file.file_url]" fit="cover" class="attachment-image" lazy/>
            <div v-else-if="file.file_type === 'VIDEO'" class="video-thumbnail" @click="playVideo(file.file_url)">
              <el-image :src="file.thumbnail_url" fit="cover" class="attachment-image">
                <template #error>
                  <div class="image-slot">视频封面加载失败</div>
                </template>
              </el-image>
              <el-icon class="play-icon">
                <VideoPlay/>
              </el-icon>
            </div>
            <el-link v-else :href="file.file_url" target="_blank" type="primary" :underline="false" class="file-link">
              <el-icon>
                <Paperclip/>
              </el-icon>
              <span class="file-name">{{ file.original_name }}</span>
            </el-link>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="comments-section" v-if="post">
      <template #header>
        <span>{{ post.comment_count || 0 }} 条评论</span>
      </template>

      <div class="comment-composer" ref="composerRef">
        <el-avatar :src="userStore.user?.avatar || defaultAvatar"/>
        <div class="composer-input-wrapper">
          <v-md-editor
              v-model="newComment.content"
              height="150px"
              :placeholder="newComment.placeholder"
          ></v-md-editor>
          <div class="composer-actions">
            <el-switch v-model="newComment.is_anonymous" active-text="匿名评论"/>
            <div>
              <el-button v-if="newComment.parent_comment" @click="cancelReply" size="small">取消回复</el-button>
              <el-button type="primary" @click="submitComment" :loading="submittingComment">发表评论</el-button>
            </div>
          </div>
        </div>
      </div>

      <div class="comments-list" v-if="post.comments && post.comments.length > 0">
        <div v-if="pinnedComments.length > 0" class="pinned-comments-wrapper">
          <el-divider content-position="left">
            <el-icon>
              <HotWater/>
            </el-icon>
            热门评论
          </el-divider>
          <div v-for="comment in pinnedComments" :key="comment.id" class="comment-item">
            <CommentItem :comment="comment" :post-id="postId" @reply="replyToComment"/>
          </div>
        </div>

        <div v-if="regularComments.length > 0" class="regular-comments-wrapper">
          <el-divider content-position="left">
            {{ pinnedComments.length > 0 ? '最新评论' : '全部评论' }}
          </el-divider>
          <div v-for="comment in regularComments" :key="comment.id" class="comment-item">
            <CommentItem :comment="comment" :post-id="postId" @reply="replyToComment"/>
          </div>
        </div>
      </div>
      <el-empty v-else description="还没有评论，快来发表你的看法吧！"/>
    </el-card>

    <el-dialog v-model="videoDialog.visible" :title="videoDialog.title" width="60%" destroy-on-close center>
      <video v-if="videoDialog.url" :src="videoDialog.url" controls autoplay style="width: 100%;"></video>
    </el-dialog>
  </div>
</template>

<script setup>
import {computed, onMounted, ref, reactive, provide, inject} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {useUserStore} from '@/store/user';
// API导入修正
import {fetchPostById, createComment, likePost, unlikePost, likeComment, unlikeComment} from '@/api/forum';
import {
  StarFilled, VideoPlay, Paperclip, HotWater
} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import DOMPurify from 'dompurify';
import MarkdownIt from 'markdown-it';
import VMdEditor from '@kangc/v-md-editor/lib/base-editor';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';

// 子组件，用于渲染单条评论，避免模板过长
const CommentItem = {
  props: ['comment', 'postId'],
  emits: ['reply'],
  setup(props, {emit}) {
    const md = new MarkdownIt();
    const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
    const post = inject('post'); // 从父组件注入整个帖子数据

    const formatTime = (time) => dayjs(time).fromNow();
    const renderedContent = computed(() => DOMPurify.sanitize(md.render(props.comment.content)));
    const allComments = computed(() => post.value?.comments || []);

    const getParentAuthorName = (parentId) => {
      const parent = allComments.value.find(c => c.id === parentId);
      return parent ? parent.author?.real_name || '匿名用户' : '原评论';
    };

    const handleCommentLike = async (comment) => {
      try {
        const apiCall = comment.is_liked ? unlikeComment : likeComment;
        const res = await apiCall(props.postId, comment.id);
        comment.like_count = res.data.like_count;
        comment.is_liked = !comment.is_liked;
      } catch (error) {
        ElMessage.error('操作失败');
      }
    };

    return {
      formatTime,
      renderedContent,
      getParentAuthorName,
      handleCommentLike,
      defaultAvatar,
      emit,
    };
  },
  template: `
    <div class="comment-item-inner">
      <el-avatar :size="32" :src="comment.author.avatar || defaultAvatar"/>
      <div class="comment-body">
        <div class="comment-header">
          <span class="comment-author">{{ comment.author.real_name || '匿名用户' }}</span>
          <el-tag v-if="comment.is_ai_generated" size="small">AI助教</el-tag>
          <div v-if="comment.parent_comment" class="reply-to">
            回复 <span class="reply-author">@{{ getParentAuthorName(comment.parent_comment) }}</span>
          </div>
        </div>
        <div class="comment-content markdown-body" v-html="renderedContent"></div>
        <div class="comment-footer">
          <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          <div class="comment-actions">
            <el-button text :type="comment.is_liked ? 'primary' : ''" :icon="StarFilled"
                       @click="handleCommentLike(comment)">
              {{ comment.like_count || '' }}
            </el-button>
            <el-button text @click="emit('reply', comment)">回复</el-button>
          </div>
        </div>
      </div>
    </div>
  `
};


// 父组件逻辑
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const md = new MarkdownIt();
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const postId = route.params.postId;
const post = ref(null);
const loading = ref(true);
const submittingComment = ref(false);
const composerRef = ref(null);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const newComment = reactive({
  content: '',
  is_anonymous: true,
  parent_comment: null,
  placeholder: '发表你的看法...',
});

const videoDialog = reactive({
  visible: false,
  title: '视频播放',
  url: '',
});

provide('post', post); // 注入post数据供子组件使用

// --- Computed Properties ---
const purifiedContent = computed(() => {
  if (post.value?.content) {
    return DOMPurify.sanitize(md.render(post.value.content));
  }
  return '';
});

const allCommentsWithFloor = computed(() =>
    (post.value?.comments || []).map((c, index) => ({...c, floor: index + 1}))
);

const primaryComments = computed(() =>
    allCommentsWithFloor.value.filter(c => !c.parent_comment)
);

const pinnedComments = computed(() => {
  if (!post.value) return [];
  // 筛选出点赞数大于0的一级评论，按点赞数排序，取前3
  return [...primaryComments.value]
      .filter(c => c.like_count > 0)
      .sort((a, b) => b.like_count - a.like_count)
      .slice(0, 3);
});

const regularComments = computed(() => {
  if (!post.value) return [];
  const pinnedIds = new Set(pinnedComments.value.map(c => c.id));
  // 过滤掉已置顶的评论，按时间正序排序
  return primaryComments.value
      .filter(c => !pinnedIds.has(c.id))
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
});


// --- Methods ---
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

const togglePostLike = async () => {
  if (!post.value) return;
  try {
    const apiCall = post.value.is_liked ? unlikePost : likePost;
    await apiCall(postId);
    post.value.like_count += post.value.is_liked ? -1 : 1;
    post.value.is_liked = !post.value.is_liked;
  } catch (error) {
    ElMessage.error('操作失败');
  }
};

const submitComment = async () => {
  if (!newComment.content.trim()) {
    return ElMessage.warning('评论内容不能为空');
  }
  submittingComment.value = true;
  try {
    const payload = {
      content: newComment.content,
      is_anonymous: newComment.is_anonymous,
      parent_comment: newComment.parent_comment,
    };
    await createComment(postId, payload);
    ElMessage.success('评论成功！');
    cancelReply(); // 清空评论框
    await loadPost(); // 重新加载数据
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '评论失败');
  } finally {
    submittingComment.value = false;
  }
};

const replyToComment = (comment) => {
  newComment.parent_comment = comment.id;
  const authorName = comment.author?.real_name || '匿名用户';
  newComment.placeholder = `回复 @${authorName}`;
  composerRef.value?.scrollIntoView({behavior: 'smooth'});
};

const cancelReply = () => {
  newComment.content = '';
  newComment.parent_comment = null;
  newComment.placeholder = '发表你的看法...';
};

const playVideo = (url) => {
  if (!url) return;
  videoDialog.url = url;
  videoDialog.visible = true;
};

onMounted(loadPost);
</script>

<style scoped>
/* 基本布局 */
.post-detail-page {
  max-width: 960px;
  margin: 20px auto;
  padding: 0 15px;
}

.page-header {
  margin-bottom: 20px;
}

.post-card, .comments-section {
  margin-bottom: 20px;
}

.markdown-body {
  line-height: 1.8;
  word-break: break-word;
}

/* 帖子头部 */
.post-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 20px;
}

.author-meta {
  display: flex;
  align-items: center;
}

.author-info {
  margin-left: 12px;
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

/* 帖子附件 */
.post-attachments {
  margin-top: 20px;
}

.attachment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.attachment-image {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  background-color: #f0f2f5;
  object-fit: cover;
}

.video-thumbnail {
  position: relative;
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
}

.play-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 40px;
  color: white;
  background-color: rgba(0, 0, 0, 0.4);
  border-radius: 50%;
  padding: 5px;
}

.file-link {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 评论区 */
.comment-composer {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.composer-input-wrapper {
  flex-grow: 1;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.comment-item {
  padding: 15px 0;
  border-top: 1px solid #f0f2f5;
}

.comment-item-inner {
  display: flex;
  gap: 15px;
}

.comment-body {
  flex-grow: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.comment-author {
  font-weight: 500;
  font-size: 0.95rem;
}

.reply-to {
  font-size: 0.9rem;
  color: #555;
}

.reply-author {
  color: #409eff;
  font-weight: 500;
}

.comment-content {
  margin: 8px 0;
  font-size: 0.95rem;
}

.comment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #8590a6;
  font-size: 0.8rem;
}

.comment-actions {
  display: flex;
  align-items: center;
}
</style>