<template>
  <div class="sent-container">
    <div class="sent-header">
      <h2>已发送</h2>
      <el-input
        v-model="searchQuery"
        placeholder="搜索收件人或主题"
        :prefix-icon="Search"
        @keyup.enter="loadSentNotifications"
        clearable
        @clear="loadSentNotifications"
        style="width: 300px;"
      />
    </div>

    <el-table
      :data="sentNotifications"
      v-loading="loading"
      style="width: 100%"
      @row-click="viewMessage"
    >
      <el-table-column prop="recipient_info.name" label="收件人" width="180" />
      <el-table-column prop="title" label="主题" />
      <el-table-column prop="timestamp" label="发送时间" width="200">
        <template #default="scope">
          {{ formatTime(scope.row.timestamp) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.is_read" type="info">已读</el-tag>
          <el-tag v-else type="success">未读</el-tag>
        </template>
      </el-table-column>
    </el-table>

    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchSentNotifications } from '@/api/notifications'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const loading = ref(false)
const sentNotifications = ref([])
const searchQuery = ref('')

const loadSentNotifications = async () => {
  loading.value = true
  try {
    const params = { search: searchQuery.value }
    const response = await fetchSentNotifications(params)
    sentNotifications.value = response.data
  } catch (error) {
    ElMessage.error('加载已发送消息失败')
  } finally {
    loading.value = false
  }
}

const viewMessage = (row) => {
  router.push({ name: 'StudentMessageView', params: { id: row.id } })
}

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

onMounted(loadSentNotifications)
</script>

<style scoped>
.sent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>