<template>
  <div class="inbox-container">
    <div class="inbox-header">
      <h2>收件箱</h2>
      <el-button-group>
        <el-button :icon="Refresh" @click="loadNotifications" :loading="loading">刷新</el-button>
        <el-button type="primary" @click="handleMarkAllRead">全部标为已读</el-button>
      </el-button-group>
    </div>

    <el-table
        :data="notifications"
        v-loading="loading"
        style="width: 100%"
        @row-click="viewMessage"
        :row-class-name="tableRowClassName"
    >
      <el-table-column prop="sender_info.name" label="发件人" width="180"/>
      <el-table-column prop="title" label="主题"/>
      <el-table-column prop="timestamp" label="时间" width="200">
        <template #default="scope">
          {{ formatTime(scope.row.timestamp) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button
              v-if="scope.row.can_recipient_delete"
              type="danger"
              size="small"
              @click.stop="handleDelete(scope.row.id)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {fetchNotifications, markAllAsRead, deleteNotification} from '@/api/notifications'
import {useNotificationStore} from '@/store/notifications'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Refresh} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const router = useRouter()
const notificationStore = useNotificationStore()
const loading = ref(false)
const notifications = ref([])
const pagination = ref({page: 1, page_size: 15, total: 0})

const loadNotifications = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    const response = await fetchNotifications(params)
    // 后端未使用DRF分页，前端进行模拟
    // 实际应由后端分页，此处为兼容后端未分页的情况
    pagination.value.total = response.data.length
    notifications.value = response.data

    // 如果后端支持DRF分页，应使用如下代码：
    // notifications.value = response.data.results
    // pagination.value.total = response.data.count

  } catch (error) {
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page) => {
  pagination.value.page = page
  loadNotifications()
}

const handleMarkAllRead = async () => {
  await markAllAsRead()
  ElMessage.success('已将所有消息标记为已读')
  loadNotifications()
  notificationStore.updateUnreadCount()
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除此条消息吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await deleteNotification(id)
    ElMessage.success('删除成功')
    loadNotifications()
  })
}

const viewMessage = (row) => {
  router.push({name: 'TeacherMessageView', params: {id: row.id}})
}

const tableRowClassName = ({row}) => {
  return !row.is_read ? 'unread-row' : ''
}

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

onMounted(loadNotifications)
</script>

<style>
.inbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.el-table .unread-row {
  font-weight: bold;
}
</style>