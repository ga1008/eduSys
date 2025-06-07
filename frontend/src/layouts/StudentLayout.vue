<template>
  <div class="student-layout">
    <div class="sidebar-container">
      <Sidebar :items="menuItemsWithBadge"/>
    </div>
    <div class="content">
      <router-view/>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, onUnmounted} from 'vue';
import {useNotificationStore} from '@/store/notifications';
import Sidebar from '@/components/Sidebar.vue';

// 实例化通知 store
const notificationStore = useNotificationStore();

// 定义原始菜单项，新增“信息中心”
const menuItems = [
  {label: '首页', path: '/student'},
  {label: '我的课程', path: '/student/courses'},
  {label: '我的作业', path: '/student/assignments'},
  {label: '信息中心', path: '/student/messages'},
];

// 创建计算属性，为“信息中心”动态添加角标
const menuItemsWithBadge = computed(() => {
  return menuItems.map(item => {
    if (item.path === '/student/messages') {
      return {
        ...item,
        badge: notificationStore.unreadCount > 0 ? notificationStore.unreadCount : ''
      };
    }
    return item;
  });
});

// 组件挂载时开始轮询未读消息数
onMounted(() => {
  notificationStore.startPolling();
});

// 组件卸载时停止轮询，避免内存泄漏
onUnmounted(() => {
  notificationStore.stopPolling();
});
</script>

<style scoped>
.student-layout {
  display: flex;
  min-height: calc(100vh - 50px);
}

.sidebar-container {
  width: 200px;
  flex-shrink: 0;
}

.content {
  flex: 1;
  padding: 20px;
  background-color: #f0f2f5;
}
</style>