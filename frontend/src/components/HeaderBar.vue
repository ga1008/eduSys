<template>
  <div class="header-bar">
    <div class="logo">{{ title }}</div>
    <div class="spacer"></div>

    <el-dropdown trigger="click" @visible-change="handleDropdownVisible" class="notification-dropdown">
      <span class="notification-icon">
        <el-badge :value="notificationStore.unreadCount" :max="99" :hidden="notificationStore.unreadCount === 0">
          <el-icon :size="22"><Bell/></el-icon>
        </el-badge>
      </span>
      <template #dropdown>
        <el-dropdown-menu>
          <div class="dropdown-header">
            <span>消息通知</span>
          </div>
          <el-scrollbar max-height="300px" v-loading="loadingNotifications">
            <el-dropdown-item
                v-if="recentNotifications.length === 0"
                disabled>
              暂无新消息
            </el-dropdown-item>
            <el-dropdown-item
                v-for="item in recentNotifications"
                :key="item.id"
                @click="navigateToMessage(item.id)">
              <div class="notification-item">
                <p class="notification-title" :class="{ 'is-unread': !item.is_read }">{{ item.title }}</p>
                <p class="notification-time">{{ formatTime(item.timestamp) }}</p>
              </div>
            </el-dropdown-item>
          </el-scrollbar>
          <div class="dropdown-footer" @click="navigateToMessageCenter">
            查看全部消息
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <div v-if="user" class="user-info">
      <span>{{ user.name || user.username }}</span>
      <span @click="handleLogout" class="logout">退出</span>
    </div>
  </div>
</template>

<script setup>
import {ref, computed} from 'vue'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/store/user'
import {useNotificationStore} from '@/store/notifications' // 引入通知store
import {fetchNotifications} from '@/api/notifications' // 引入通知API
import {ElMessageBox} from 'element-plus'
import {Bell} from '@element-plus/icons-vue' // 引入图标
import dayjs from 'dayjs'

const userStore = useUserStore()
const notificationStore = useNotificationStore() // 使用通知store
const router = useRouter() // 使用路由

const user = computed(() => userStore.user)
const title = '在线教育平台'

const recentNotifications = ref([])
const loadingNotifications = ref(false)

// 格式化时间
const formatTime = (time) => dayjs(time).fromNow() // 使用 fromNow 更友好，例如 "5分钟前"

// 处理登出
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {type: 'warning'})
      .then(() => userStore.logout())
      .catch(() => {
      }) // 取消
}

// 获取最近的5条通知
const loadRecentNotifications = async () => {
  if (loadingNotifications.value) return
  loadingNotifications.value = true
  try {
    // 获取最新的5条通知，无论是否已读
    const response = await fetchNotifications({page: 1, page_size: 5})
    recentNotifications.value = response.data // 假设后端未分页，直接取data
    // 如果后端分页，则用 response.data.results
  } catch (error) {
    console.error('获取最近通知失败', error)
  } finally {
    loadingNotifications.value = false
  }
}

// 当下拉菜单显示/隐藏时触发
const handleDropdownVisible = (visible) => {
  // 当下拉菜单打开时，加载最新消息
  if (visible) {
    loadRecentNotifications()
  }
}

// 跳转到具体消息页面
const navigateToMessage = (id) => {
  router.push({name: 'TeacherMessageView', params: {id}})
}

// 跳转到信息中心
const navigateToMessageCenter = () => {
  router.push({name: 'TeacherMessageInbox'})
}

</script>

<style scoped>
.header-bar {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 50px;
  background-color: #409EFF;
  color: #fff;
}

.logo {
  font-size: 18px;
  font-weight: bold;
}

.spacer {
  flex: 1;
}

/* 通知图标样式 */
.notification-dropdown {
  margin-right: 25px;
}

.notification-icon {
  cursor: pointer;
  color: #fff;
}

.notification-icon .el-icon {
  vertical-align: middle;
}

/* 用户信息 */
.user-info {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.user-info span {
  vertical-align: middle;
}

.logout {
  margin-left: 15px;
  cursor: pointer;
  text-decoration: underline;
}

.logout:hover {
  opacity: 0.8;
}

/* 下拉菜单样式 */
.dropdown-header, .dropdown-footer {
  padding: 8px 12px;
  text-align: center;
  font-size: 14px;
  color: #333;
}

.dropdown-header {
  border-bottom: 1px solid #ebeef5;
}

.dropdown-footer {
  border-top: 1px solid #ebeef5;
  cursor: pointer;
}

.dropdown-footer:hover {
  background-color: #ecf5ff;
}

.notification-item {
  line-height: 1.4;
}

.notification-title {
  font-size: 14px;
  color: #303133;
  white-space: normal;
}

.notification-title.is-unread {
  font-weight: bold;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}
</style>