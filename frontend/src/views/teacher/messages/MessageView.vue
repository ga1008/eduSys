<template>
  <div v-if="loading" v-loading="loading" class="message-view-loading"></div>
  <div v-else-if="message" class="message-view">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">{{ message.title }}</span>
      </template>
      <template #extra>
        <div class="header-actions">
          <el-button
              v-if="isSender && canRetract"
              type="warning"
              :icon="RefreshLeft"
              @click="handleRetract"
              :loading="retracting"
          >
            撤回消息
          </el-button>
          <el-button
              v-if="!isSender"
              type="danger"
              plain
              :icon="CircleClose"
              @click="handleBlockSender"
          >
            屏蔽发件人
          </el-button>
        </div>
      </template>
    </el-page-header>

    <div class="message-meta">
      <p v-if="isSender"><strong>收件人:</strong> {{ message.recipient_info.name }}</p>
      <p v-else><strong>发件人:</strong> {{ message.sender_info.name }}</p>
      <p><strong>时间:</strong> {{ formatTime(message.timestamp) }}</p>
    </div>

    <el-card class="message-content-card" shadow="never">
      <div v-html="renderedContent" class="markdown-body"></div>
    </el-card>

    <div v-if="!isSender && message.can_recipient_reply" class="reply-section">
      <h3>回复消息</h3>
      <v-md-editor
          v-model="replyContent"
          height="250px"
          placeholder="输入回复内容，支持 Markdown 格式..."
          left-toolbar="undo redo | bold italic strikethrough | quote ul ol | link"
      ></v-md-editor>
      <el-button type="primary" @click="handleReply" :loading="replying" class="reply-btn">
        发送回复
      </el-button>
    </div>
  </div>
</template>

<script setup>
// --- 核心库导入 ---
import {ref, onMounted, computed} from 'vue';
import {useRoute, useRouter} from 'vue-router';

// --- Pinia 状态管理导入 ---
import {useUserStore} from '@/store/user';
import {useNotificationStore} from '@/store/notifications';

// --- API 函数导入 ---
import {
  blockSenderFromNotification,
  fetchNotificationById,
  markAsRead,
  replyToMessage,
  retractMessage
} from '@/api/notifications';

// --- UI & 图标库导入 ---
import {ElMessage, ElMessageBox} from 'element-plus';
import {RefreshLeft, CircleClose} from '@element-plus/icons-vue';

// --- 第三方工具库导入 ---
import dayjs from 'dayjs';
import DOMPurify from 'dompurify';

// --- Markdown 渲染与编辑相关导入 ---
import MarkdownIt from 'markdown-it';
import VMdEditor from '@kangc/v-md-editor/lib/base-editor';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import Prism from 'prismjs';
import markdownItPrism from 'markdown-it-prism';

// 样式
import '@kangc/v-md-editor/lib/style/base-editor.css';
import '@kangc/v-md-editor/lib/theme/style/github.css';
import 'prismjs/themes/prism.css';

// Prism.js 语言模块 (按依赖顺序)
// 基础依赖 (必须先导入)
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-javascript';
// 依赖于基础的语言
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-typescript';
// 其他语言
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-python';

// --- 初始化与插件注册 ---
VMdEditor.use(githubTheme, {Prism});
const md = new MarkdownIt().use(markdownItPrism);

// --- 路由与状态管理实例 ---
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const notificationStore = useNotificationStore();

// --- 组件响应式状态 ---
const loading = ref(true);
const replying = ref(false);
const retracting = ref(false);
const message = ref(null);
const replyContent = ref('');
const messageId = route.params.id;

// --- 计算属性 ---
// 安全地渲染Markdown内容
const renderedContent = computed(() => {
  if (message.value && message.value.content) {
    const rawHtml = md.render(message.value.content);
    return DOMPurify.sanitize(rawHtml);
  }
  return '';
});

// 判断当前用户是否为发件人
const isSender = computed(() => {
  return message.value && userStore.user.id === message.value.sender_info.id;
});

// 判断消息是否可撤回 (10分钟内且未读)
const canRetract = computed(() => {
  if (!message.value || !isSender.value) return false;
  const sentTime = dayjs(message.value.timestamp);
  return dayjs().diff(sentTime, 'minute') < 10 && !message.value.is_read;
});

// --- 核心业务函数 ---
// 加载消息详情
const loadMessage = async () => {
  loading.value = true;
  try {
    const response = await fetchNotificationById(messageId);
    message.value = response.data;
    if (!isSender.value && message.value && !message.value.is_read) {
      await markAsRead(messageId);
      notificationStore.updateUnreadCount();
    }
  } catch (error) {
    ElMessage.error('加载消息详情失败');
    console.error("加载消息失败:", error);
  } finally {
    loading.value = false;
  }
};

// 发送回复
const handleReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('回复内容不能为空');
    return;
  }
  replying.value = true;
  try {
    await replyToMessage(messageId, {content: replyContent.value});
    ElMessage.success('回复成功');
    replyContent.value = '';
    await loadMessage(); // 重新加载消息以更新状态
  } catch (error) {
    console.error("回复失败:", error);
  } finally {
    replying.value = false;
  }
};

// 撤回消息
const handleRetract = () => {
  ElMessageBox.confirm('确定要撤回这条消息吗？撤回后对方将无法看到。', '确认撤回', {
    type: 'warning'
  }).then(async () => {
    retracting.value = true;
    try {
      await retractMessage(messageId);
      ElMessage.success('撤回成功');
      router.push({name: 'TeacherMessageSent'}); // 跳转到教师已发送列表
    } finally {
      retracting.value = false;
    }
  }).catch(() => {
  });
};

// 屏蔽发件人
const handleBlockSender = () => {
  if (!message.value?.sender_info) return;
  const senderName = message.value.sender_info.name || message.value.sender_info.username;
  ElMessageBox.confirm(`确定要屏蔽来自「${senderName}」的所有消息吗？`, '屏蔽确认', {
    confirmButtonText: '确定屏蔽',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await blockSenderFromNotification(messageId);
      ElMessage.success(`已成功屏蔽 ${senderName}`);
      router.push({name: 'TeacherMessageInbox'}); // 跳转到教师收件箱
    } catch (error) {
      console.error("屏蔽失败:", error);
    }
  }).catch(() => {
  });
};

// --- 工具函数 ---
const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss');

// --- 生命周期钩子 ---
onMounted(loadMessage);
</script>

<style scoped>
/* 复制之前优化过的样式，确保体验统一 */
.message-view {
  max-width: 960px;
  margin: 0 auto;
}

.message-view-loading {
  min-height: 400px;
}

.page-title {
  font-size: 20px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
}

.message-meta {
  margin-top: 24px;
  padding: 12px 20px;
  background-color: #f7f7f7;
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
  display: flex;
  gap: 24px;
}

.message-meta p {
  margin: 0;
}

.message-content-card {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.reply-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.reply-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
  font-weight: 500;
}

.reply-btn {
  margin-top: 15px;
}

/* --- 全面优化的 Markdown 渲染样式 (与学生端保持一致) --- */
.markdown-body {
  line-height: 1.75;
  color: #333;
  font-size: 15px;
  padding: 2px 5px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h2) {
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}

.markdown-body :deep(p) {
  margin-bottom: 16px;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 2em;
  margin-bottom: 16px;
}

.markdown-body :deep(blockquote) {
  border-left: 0.25em solid #dfe2e5;
  padding: 0 1em;
  color: #6a737d;
  margin-left: 0;
  margin-right: 0;
  margin-bottom: 16px;
}

.markdown-body :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  background-color: rgba(27, 31, 35, 0.05);
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  border-radius: 6px;
}

.markdown-body :deep(pre) {
  margin-bottom: 16px;
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 6px;
}

.markdown-body :deep(pre code) {
  display: inline;
  padding: 0;
  margin: 0;
  overflow: visible;
  line-height: inherit;
  word-wrap: normal;
  background-color: transparent;
  border: 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
}

.markdown-body :deep(th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.markdown-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}
</style>