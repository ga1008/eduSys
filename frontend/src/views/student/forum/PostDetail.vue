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
            <span class="author-name">{{ getAuthorName(post.author) }}</span>
            <el-tag class="post-time" style="margin-left: 10px">{{ formatTime(post.created_at) }}</el-tag>
            <el-tag class="post-view-count" style="margin-left: 10px">围观 {{ post.view_count }}</el-tag>
            <el-tag class="post-comment-count" style="margin-left: 10px">花生 {{ post.comment_count }}</el-tag>
          </div>
          <div class="post-actions">
            <el-button :type="post.is_liked ? 'primary' : 'default'" :icon="CaretTop" @click="togglePostLike" round>
              点赞 {{ post.like_count }}
            </el-button>
            <el-tag v-for="tag in post.tags" :key="tag.id" size="small" type="success" effect="plain">
              {{ tag.name }}
            </el-tag>
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
              left-toolbar="undo redo | bold italic | quote"
              right-toolbar=""
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
          <CommentItem v-for="comment in pinnedComments" :key="comment.id" :comment="comment" @reply="replyToComment"
                       @toggle-like="handleToggleCommentLike"/>
        </div>

        <el-divider v-if="pinnedComments.length > 0 && regularComments.length > 0"/>

        <div v-if="regularComments.length > 0" class="regular-comments-wrapper">
          <el-divider content-position="left" v-if="pinnedComments.length > 0">最新评论</el-divider>
          <CommentItem v-for="comment in regularComments" :key="comment.id" :comment="comment" @reply="replyToComment"
                       @toggle-like="handleToggleCommentLike"/>
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
import {computed, onMounted, ref, reactive, defineComponent, inject, h, provide} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElAvatar, ElButton, ElMessage, ElTag} from 'element-plus';
import {useUserStore} from '@/store/user';
import {
  fetchPostById,
  createComment,
  likePost,
  unlikePost,
  likeComment,
  unlikeComment,
  viewPost,
  fetchUserInfo
} from '@/api/forum';
// [修改] 导入新图标 CaretTop
import {CaretTop, VideoPlay, Paperclip, HotWater} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import DOMPurify from 'dompurify';
import MarkdownIt from 'markdown-it';
import VMdEditor from '@kangc/v-md-editor/lib/base-editor';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import '@kangc/v-md-editor/lib/style/base-editor.css';
import '@kangc/v-md-editor/lib/theme/style/github.css';

VMdEditor.use(githubTheme, {});
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const md = new MarkdownIt();
const author = ref(null);
const isAnonymous = ref(true);

// ✨ 评论子组件 (精简后)
const CommentItem = defineComponent({
  name: 'CommentItem',
  props: ['comment'],
  // ✨ [修改] 声明会触发的自定义事件
  emits: ['reply', 'toggle-like'],
  setup(props, {emit}) {
    const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
    const post = inject('post');

    const allComments = computed(() => post.value?.comments || []);
    const getParentAuthorName = (parentId) => {
      const parent = allComments.value.find(c => c.id === parentId);
      return parent ? (getUserName(parent.author.id) || '匿名用户') : '原评论';
    };

    // ✨ [移除] toggleCommentLike 函数已移至父组件

    const formatTime = (time) => dayjs(time).fromNow();

    return {
      defaultAvatar,
      getParentAuthorName,
      formatTime,
      emit, // 需要返回 emit 才能在 render 函数中使用
    };
  },
  render() {
    const {comment} = this;
    const renderedContent = DOMPurify.sanitize(md.render(this.comment.content));

    return h('div', {class: 'comment-item-inner'}, [
      h(ElAvatar, {size: 32, src: comment.author.avatar || this.defaultAvatar}),
      h('div', {class: 'comment-body'}, [
        h('div', {class: 'comment-header'}, [

          h(
              'span',
              {
                class: 'floor-number', style: {
                  marginRight: '5px',
                  color: '#aaa',
                  fontSize: '0.8rem',
                  borderRight: '1px solid #e0e0e0',
                  padding: '0 5px'
                }
              },
              `${comment.floor} 楼`
          ),
          // 如果回复人id是发帖人id并且不是匿名状态，则显示“楼主”字样
          comment.author.id === author.value.id && !isAnonymous.value
              ? h(
                  'span',
                  {
                    class: 'comment-author-tag',
                    style: {
                      border: '1px solid #e0e0e0',
                      padding: '2px 5px',
                      borderRadius: '5px',
                      fontSize: '0.8rem',
                      color: '#409eff',
                      marginRight: '5px'
                    }
                  },
                  '楼主'
              )
              : null,
          h('span', {class: 'comment-author'}, getCommentUserName(comment)),
          comment.is_ai_generated ? h(ElTag, {size: 'small'}, () => 'AI助教') : null,
          comment.parent_comment ? h('div', {class: 'reply-to'}, [
            '回复 ', h('span', {class: 'reply-author'}, `@${this.getParentAuthorName(comment.parent_comment)}`)
          ]) : null,
        ]),
        h('div', {class: 'comment-content markdown-body', innerHTML: renderedContent}),
        h('div', {class: 'comment-footer'}, [
          h('span', {class: 'comment-time'}, this.formatTime(comment.created_at)),
          h('div', {class: 'comment-actions'}, [
            h(ElButton, {
              round: true,
              size: 'small',
              type: comment.is_liked ? 'primary' : '',
              icon: CaretTop,
              onClick: () => this.emit('toggle-like', comment) // ✨ 上报事件，传递整个评论对象
            }, () => comment.like_count || '赞'),
            // [修改] 统一回复按钮尺寸
            h(ElButton, {text: true, size: 'small', onClick: () => this.emit('reply', comment)}, () => '回复')
          ])
        ])
      ])
    ]);
  }
});


const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const postId = route.params.postId;
const post = ref(null);
const loading = ref(true);
const submittingComment = ref(false);
const composerRef = ref(null);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const users = ref([]); // 用于存储用户信息，后续可扩展

const newComment = reactive({
  content: '',
  is_anonymous: true,
  parent_comment: null,
  placeholder: '发表你的看法...',
});

const videoDialog = reactive({
  visible: false,
  title: '',
  url: '',
});

provide('post', post);

const purifiedContent = computed(() => {
  return post.value?.content ? DOMPurify.sanitize(md.render(post.value.content)) : '';
});

const allCommentsWithFloor = computed(() =>
    (post.value?.comments || []).map((c, index) => ({...c, floor: index + 1}))
);

const primaryComments = computed(() => allCommentsWithFloor.value.filter(c => !c.parent_comment));

const pinnedComments = computed(() => {
  return [...primaryComments.value]
      .filter(c => c.like_count > 0)
      .sort((a, b) => b.like_count - a.like_count)
      .slice(0, 3);
});

const regularComments = computed(() => {
  const pinnedIds = new Set(pinnedComments.value.map(c => c.id));
  return primaryComments.value
      .filter(c => !pinnedIds.has(c.id))
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
});

// 查看所有的评论，根据是否是楼主改变 comment-author-tag 的样式


const getAuthorName = (author) => {
  if (isAnonymous.value) return '无名';
  if (!author || !author.id) return '无名';
  return author.class_name + " " + author.name;
};

const getCommentUserName = (comment) => {
  if (!comment.author || !comment.author.id) return '无名';
  return comment.author.class_name + " " + comment.author.name
};

const getUserName = (userId) => {
  for (const user of users.value) {
    if (user.id === userId) {
      return user.real_name || '匿名用户';
    }
  }
  updateUserInfo(userId);
  return '加载中...';
};

const updateUserInfo = async (userId) => {
  if (!userId) return;
  const userInfo = await getUserInfo(userId);
  if (userInfo) {
    // 如果用户信息已存在，则更新
    const existingUser = users.value.find(u => u.id === userId);
    if (existingUser) {
      Object.assign(existingUser, userInfo);
    } else {
      users.value.push(userInfo);
    }
  }
};


const getUserInfo = async (userId) => {
  try {
    const res = await fetchUserInfo(userId);
    return res.data;
  } catch (error) {
    ElMessage.error('获取用户信息失败');
    return null;
  }
};

const loadPost = async () => {
  loading.value = true;
  try {
    const res = await fetchPostById(postId);
    post.value = res.data;
    author.value = post.value.author;
    isAnonymous.value = post.value.is_anonymous;

    await viewPost(postId); // 记录浏览量
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
  const apiCall = post.value.is_liked ? unlikePost : likePost;
  try {
    // 帖子的点赞可以直接修改，因为它不是props
    const res = await apiCall(postId);
    post.value.like_count = res.data.like_count;
    post.value.is_liked = res.data.is_liked;
  } catch (error) {
    ElMessage.error('操作失败');
  }
};

// ✨ [新增] 处理评论点赞的函数，由父组件统一管理
const handleToggleCommentLike = async (comment) => {
  if (!post.value) return;
  try {
    const apiCall = comment.is_liked ? unlikeComment : likeComment;
    const res = await apiCall(post.value.id, comment.id);

    // 直接修改 comment 对象（它是 post.value.comments 数组中的一个引用）
    comment.like_count = res.data.like_count;
    comment.is_liked = res.data.is_liked;

  } catch (error) {
    ElMessage.error('操作失败');
  }
};

const submitComment = async () => {
  if (!newComment.content.trim()) return ElMessage.warning('评论内容不能为空');
  submittingComment.value = true;
  try {
    await createComment(postId, {...newComment});
    ElMessage.success('评论成功！');
    cancelReply();
    await loadPost();
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '评论失败');
  } finally {
    submittingComment.value = false;
  }
};

const replyToComment = (comment) => {
  newComment.parent_comment = comment.id;
  newComment.placeholder = `回复 @${comment.author.real_name || '匿名用户'}`;
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
  videoDialog.title = '视频预览';
  videoDialog.visible = true;
};

onMounted(loadPost);
</script>


<style scoped>
/* ✨ 1. 使用 CSS 变量统一管理颜色和间距，方便维护 */
.post-detail-page {
  --text-color-primary: #303133;
  --text-color-secondary: #8590a6;
  --border-color-light: #f0f2f5;
  --primary-brand-color: #409eff;
  --card-border-radius: 8px;
  --spacing-small: 8px;
  --spacing-medium: 12px;
  --spacing-large: 20px;

  max-width: 960px;
  margin: var(--spacing-large) auto;
  padding: 0 15px;
}

.page-header {
  margin-bottom: var(--spacing-large);
}

.post-card, .comments-section {
  margin-bottom: var(--spacing-large);
  border-radius: var(--card-border-radius);
}

.markdown-body {
  line-height: 1.8;
  word-break: break-word;
}

.post-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: var(--spacing-large);
}

.author-meta {
  display: flex;
  align-items: center;
}

.author-info {
  margin-left: var(--spacing-medium);
}

.author-name {
  font-weight: 500;
}

.post-time .post-view-count {
  font-size: 0.8rem;
  color: var(--text-color-secondary);
}

.post-actions {
  margin-left: auto;
}

.post-content {
  padding: 10px 0;
}

.post-attachments {
  margin-top: var(--spacing-large);
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
  background-color: var(--border-color-light);
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
  padding: var(--spacing-small);
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.file-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

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

/* .comment-item 样式在 render 函数中未被使用，但保留以备将来扩展 */
.comment-item {
  padding: 15px 0;
  border-top: 1px solid var(--border-color-light);
}

.comment-item-inner {
  display: flex;
  gap: 15px;
  /* ✨ 为每个评论添加上边距和上边框，除了第一个 */
  padding-top: var(--spacing-large);
  margin-top: var(--spacing-large);
  border-top: 1px solid var(--border-color-light);
}

/* ✨ 使用 :first-of-type 伪类移除第一个评论项的上边框和边距，使布局更干净 */
.comments-list .comment-item-inner:first-of-type {
  margin-top: 0;
  padding-top: 0;
  border-top: none;
}

.comment-body {
  flex-grow: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-small);
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.comment-author {
  font-weight: 500;
  font-size: 0.95rem;
}

.floor-number {
  color: #aaa;
  font-size: 0.8rem;
  margin-left: 5px;
}

.reply-to {
  font-size: 0.9rem;
  color: #555;
}

.reply-author {
  color: var(--primary-brand-color);
  font-weight: 500;
}

.comment-content {
  margin: var(--spacing-small) 0;
  font-size: 0.95rem;
}

.comment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-color-secondary);
  font-size: 0.8rem;
}

.comment-actions {
  display: flex;
  align-items: center;
}

/* ✨ 2. 交互优化：合并选择器并增加悬停效果 */
.post-actions .el-button,
.comment-actions .el-button {
  transition: all 0.2s ease-in-out;
}

/* 为按钮增加悬停效果，提升用户体验 */
.post-actions .el-button:hover,
.comment-actions .el-button:hover {
  filter: brightness(1.1);
}

/* 当按钮被点击或激活时，给图标一个轻微的“跳动”效果 */
.post-actions .el-button:active .el-icon,
.comment-actions .el-button:active .el-icon {
  animation: bounce-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes bounce-in {
  0% {
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}
</style>