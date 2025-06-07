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
        </div>
      </template>
    </el-page-header>

    <div class="message-header">
      <p v-if="isSender"><strong>收件人:</strong> {{ message.recipient_info.name }}</p>
      <p v-else><strong>发件人:</strong> {{ message.sender_info.name }}</p>

      <p><strong>时间:</strong> {{ formatTime(message.timestamp) }}</p>
    </div>

    <el-card class="message-content">
      <div v-html="message.content"></div>
    </el-card>

    <div v-if="!isSender && message.can_recipient_reply" class="reply-section">
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
import {ref, onMounted, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {useUserStore} from '@/store/user'
import {fetchNotificationById, markAsRead, replyToMessage, retractMessage} from '@/api/notifications'
import {useNotificationStore} from '@/store/notifications'
import {ElMessage, ElMessageBox} from 'element-plus'
import {RefreshLeft} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const loading = ref(true)
const replying = ref(false)
const retracting = ref(false)
const message = ref(null)
const replyContent = ref('')

const messageId = route.params.id

// 计算属性，判断当前登录用户是否为发件人
const isSender = computed(() => {
  return message.value && userStore.user.id === message.value.sender_info.id
})

// 计算属性，判断是否可以撤回
const canRetract = computed(() => {
  if (!message.value || isSender.value === false) return false

  const sentTime = dayjs(message.value.timestamp);
  const now = dayjs();
  // 10分钟内且对方未读
  return now.diff(sentTime, 'minute') < 10 && !message.value.is_read;
})

const loadMessage = async () => {
  loading.value = true
  try {
    const response = await fetchNotificationById(messageId)
    message.value = response.data
    // 如果是收件人，且消息未读，则标记为已读
    if (!isSender.value && !message.value.is_read) {
      await markAsRead(messageId)
      notificationStore.updateUnreadCount()
    }
  } catch (error) {
    ElMessage.error('加载消息详情失败')
  } finally {
    loading.value = false
  }
}

const handleReply = async () => {
  // ... 此处逻辑保持不变 ...
}

const handleRetract = async () => {
  ElMessageBox.confirm('确定要撤回这条消息吗？撤回后对方将无法看到。', '提示', {
    type: 'warning'
  }).then(async () => {
    retracting.value = true
    try {
      await retractMessage(messageId)
      ElMessage.success('撤回成功')
      router.push({name: 'TeacherMessageSent'}) // 返回已发送列表
    } finally {
      retracting.value = false
    }
  }).catch(() => {
  })
}

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm:ss')

onMounted(loadMessage)
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
</style>