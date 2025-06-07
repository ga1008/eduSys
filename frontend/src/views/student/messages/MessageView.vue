<!-- MessageView.vue -->
<template>
  <div v-if="loading" v-loading="loading" class="message-view-loading"></div>
  <div v-else-if="message" class="message-view">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">{{ message.title }}</span>
      </template>
      <template #extra>
        <el-button
            v-if="isSender && canRetract"
            type="warning"
            :icon="RefreshLeft"
            @click="handleRetract"
            :loading="retracting"
        >
          撤回
        </el-button>
      </template>
    </el-page-header>

    <div class="message-meta">
      <span><strong>发件人：</strong>{{ message.sender_info.name }}</span>
      <span><strong>时间：</strong>{{ formatTime(message.timestamp) }}</span>
    </div>

    <!-- 渲染 Markdown -->
    <div
        class="message-body markdown-body"
        v-html="renderedContent"
    ></div>

    <h3>回复</h3>
    <el-form>
      <el-form-item>
        <!-- Markdown 回复框 -->
        <el-input
            type="textarea"
            v-model="replyContent"
            placeholder="输入回复内容（支持 Markdown）"
            :autosize="{ minRows: 6, maxRows: 12 }"
        />
      </el-form-item>
      <el-form-item>
        <el-button
            type="primary"
            :loading="replying"
            @click="handleReply"
        >
          发送回复
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {ref, onMounted, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useUserStore} from '@/store/user'
import {useNotificationStore} from '@/store/notifications'
import {ElMessage, ElMessageBox} from 'element-plus'
import {RefreshLeft} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'
import markdownItHighlight from 'markdown-it-highlightjs'
import DOMPurify from 'dompurify'
import 'highlight.js/styles/github.css'

// 初始化 Markdown 渲染器
const md = new MarkdownIt().use(markdownItHighlight)

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const notifStore = useNotificationStore()

const messageId = route.params.id
const message = ref(null)
const loading = ref(false)
const retracting = ref(false)

const replyContent = ref('')
const replying = ref(false)

const loadMessage = async () => {
  loading.value = true
  try {
    const res = await notifStore.fetchMessage(messageId)
    message.value = res.data
  } catch (error) {
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadMessage)

const isSender = computed(() => {
  return message.value && userStore.user.id === message.value.sender_info.id
})

const canRetract = computed(() => {
  return message.value && message.value.can_retract
})

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

const renderedContent = computed(() => {
  if (message.value && message.value.content) {
    // 渲染并消毒
    const raw = md.render(message.value.content)
    return DOMPurify.sanitize(raw)
  }
  return ''
})

const handleRetract = async () => {
  const confirmed = await ElMessageBox.confirm('确认撤回此消息？', '提示')
  if (!confirmed) return
  retracting.value = true
  try {
    await notifStore.retractMessage(messageId)
    ElMessage.success('已撤回')
    router.back()
  } finally {
    retracting.value = false
  }
}

const handleReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('回复内容不能为空')
    return
  }
  replying.value = true
  try {
    // 直接发送 Markdown 文本
    await notifStore.replyToMessage(messageId, {
      content: replyContent.value
    })
    ElMessage.success('回复成功')
    replyContent.value = ''
    loadMessage()
  } catch (err) {
    console.error(err)
  } finally {
    replying.value = false
  }
}
</script>

<style scoped>
.page-title {
  font-size: 18px;
}

.header-actions {
  margin-left: 20px;
}

.message-header {
  margin-top: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  font-size: 14px;
  color: #606266;
}

.message-content {
  margin-top: 20px;
}

.reply-section {
  margin-top: 30px;
}

.reply-btn {
  margin-top: 15px;
}

/* Markdown 内容渲染样式 */

.message-meta {
  margin: 16px 0;
  color: #666;
}

.markdown-body {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
  margin-top: 24px;
  margin-bottom: 16px;
}

.markdown-body p {
  margin-bottom: 16px;
}

.markdown-body ul, .markdown-body ol {
  padding-left: 2em;
  margin-bottom: 16px;
}

.markdown-body blockquote {
  border-left: 0.25em solid #dfe2e5;
  padding: 0 1em;
  color: #6a737d;
  margin: 0 0 16px;
}

.markdown-body code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  background-color: rgba(27, 31, 35, 0.05);
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  border-radius: 3px;
}

.markdown-body pre {
  background-color: #f6f8fa;
  padding: 16px;
  overflow: auto;
  border-radius: 3px;
}

.markdown-body pre code {
  padding: 0;
  margin: 0;
  background-color: transparent;
  border: none;
}


/* QuillEditor 的自定义样式 */
.custom-quill-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid #dcdfe6; /* 添加边框以匹配 Element Plus 风格 */
  border-radius: 4px;
}

.custom-quill-editor :deep(.ql-toolbar.ql-snow) {
  border: none; /* 移除 Quill 默认工具栏边框 */
  border-bottom: 1px solid #dcdfe6; /* 在工具栏下方添加分隔线 */
  background-color: #f8f9fa;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  padding: 8px; /* 调整工具栏内边距 */
}

.custom-quill-editor :deep(.ql-container.ql-snow) {
  border: none; /* 移除 Quill 默认容器边框 */
  min-height: 200px; /* 编辑器内容区域的最小高度 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.custom-quill-editor :deep(.ql-editor) {
  padding: 12px 15px; /* 调整编辑区域内边距 */
  flex-grow: 1;
  overflow-y: auto;
  height: 100%;
  font-size: 14px; /* 统一字体大小 */
  line-height: 1.6; /* 调整行高 */
}

.message-view-loading {
  min-height: 300px; /* 给加载状态一个最小高度 */
}

</style>