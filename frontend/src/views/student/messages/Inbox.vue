<template>
  <div class="inbox-container">
    <div class="inbox-header">
      <h2>收件箱</h2>
      <el-button-group>
        <el-button :icon="Refresh" @click="loadNotifications" :loading="loading">刷新</el-button>
        <el-button type="primary" @click="handleMarkAllRead">全部标为已读</el-button>
      </el-button-group>
    </div>

    <el-table :data="notifications" v-loading="loading" style="width: 100%" @row-click="viewMessage"
              :row-class-name="tableRowClassName">
      <el-table-column prop="sender_info.name" label="发件人" width="180"/>
      <el-table-column prop="title" label="主题"/>
      <el-table-column prop="timestamp" label="时间" width="200">
        <template #default="scope">{{ formatTime(scope.row.timestamp) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button v-if="scope.row.can_recipient_delete" type="danger" size="small"
                     @click.stop="handleDelete(scope.row.id)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {useRouter} from 'vue-router';
import {fetchNotifications, markAllAsRead, deleteNotification} from '@/api/notifications';
import {useNotificationStore} from '@/store/notifications';
import {ElMessage, ElMessageBox} from 'element-plus';
import {Refresh} from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const router = useRouter();
const notificationStore = useNotificationStore();
const loading = ref(false);
const notifications = ref([]);

const loadNotifications = async () => {
  loading.value = true;
  try {
    const response = await fetchNotifications();
    notifications.value = response.data;
  } catch (error) {
    ElMessage.error('加载消息失败');
  } finally {
    loading.value = false;
  }
};

const handleMarkAllRead = async () => {
  await markAllAsRead();
  ElMessage.success('已将所有消息标记为已读');
  await loadNotifications();
  await notificationStore.updateUnreadCount();
};

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除此条消息吗？', '提示', {type: 'warning'})
      .then(async () => {
        await deleteNotification(id);
        ElMessage.success('删除成功');
        await loadNotifications();
      });
};

const viewMessage = (row) => {
  router.push({name: 'StudentMessageView', params: {id: row.id}});
};

const tableRowClassName = ({row}) => !row.is_read ? 'unread-row' : '';
const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm');

onMounted(loadNotifications);
</script>

<style>
.inbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.el-table .unread-row {
  font-weight: bold;
}
</style>