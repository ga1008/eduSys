<template>
  <div class="teacher-layout">
    <div class="sidebar-container">
      <Sidebar :items="menuItemsWithBadge"/>
    </div>
    <div class="content">
      <router-view/>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, onUnmounted} from 'vue'
import {useNotificationStore} from '@/store/notifications'
import Sidebar from '@/components/Sidebar.vue'

// 使用 setup script 语法
const notificationStore = useNotificationStore()

// 原始菜单项
const menuItems = [
  {label: '教师首页', path: '/teacher/dashboard'},
  {label: '我的课程', path: '/teacher/courses'},
  {label: '我的学生', path: '/teacher/students'},
  {label: '作业管理', path: '/teacher/courses/homeworks'},
  {label: '信息中心', path: '/teacher/messages'} // 新增信息中心
]

// 计算属性，动态为“信息中心”添加角标
const menuItemsWithBadge = computed(() => {
  return menuItems.map(item => {
    if (item.path === '/teacher/messages') {
      return {
        ...item,
        badge: notificationStore.unreadCount > 0 ? notificationStore.unreadCount : ''
      }
    }
    return item
  })
})

// 在组件挂载时开始轮询，卸载时停止
onMounted(() => {
  notificationStore.startPolling()
})

onUnmounted(() => {
  notificationStore.stopPolling()
})
</script>

<style scoped>
.teacher-layout {
  display: flex;
  min-height: calc(100vh - 50px); /* 假设顶部导航栏高度为50px */
}

.sidebar-container {
  width: 200px; /* 侧边栏宽度 */
  flex-shrink: 0; /* 防止侧边栏被压缩 */
}

.content {
  flex: 1;
  padding: 20px;
  background-color: #f0f2f5; /* 添加一个浅灰色背景，让内容区更突出 */
}
</style>