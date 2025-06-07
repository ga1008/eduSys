<template>
  <div v-if="loading" v-loading="loading" class="message-view-loading"></div>
  <div v-else-if="message" class="message-view">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">{{ message.title }}</span>
      </template>
    </el-page-header>

    <div class="message-header">
      <p><strong>发件人:</strong> {{ message.sender_info.name }}</p>
      <p><strong>时间:</strong> {{ formatTime(message.timestamp) }}</p>
    </div>

    <el-card class="message-content">
      <div v-html="message.content"></div>
    </el-card>

    <div v-if="message.can_recipient_reply" class="reply-section">
      <h3>回复</h3>
      <el-input
          v-model="replyContent"
          type="textarea"
          :rows="5"
          placeholder="输入回复内容..."
      />
      <el-button type="primary" @click="handleReply" :loading="replying" class="reply-btn">
        发送回复
      </el-button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRoute} from 'vue-router'
import {fetchNotificationById, markAsRead, replyToMessage} from '@/api/notifications'
import {useNotificationStore} from '@/store/notifications'
import {ElMessage} from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const notificationStore = useNotificationStore()
const loading = ref(true)
const replying = ref(false)
const message = ref(null)
const replyContent = ref('')

const messageId = route.params.id

const loadMessage = async () => {
  loading.value = true
  try {
    const response = await fetchNotificationById(messageId)
    message.value = response.data
    // 标记为已读
    if (!message.value.is_read) {
      await markAsRead(messageId)
      notificationStore.updateUnreadCount() // 更新全局未读数
    }
  } catch (error) {
    ElMessage.error('加载消息详情失败')
  } finally {
    loading.value = false
  }
}

const handleReply = async () => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('回复内容不能为空')
    return
  }
  replying.value = true
  try {
    await replyToMessage(messageId, {content: replyContent.value})
    ElMessage.success('回复成功')
    replyContent.value = ''
    // 可以选择刷新当前会话或提示用户已回复
  } finally {
    replying.value = false
  }
}

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')

onMounted(loadMessage)
</script>

<style scoped>
.page-title {
  font-size: 18px;
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
</style>