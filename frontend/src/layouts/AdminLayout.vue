<template>
  <div class="admin-layout">
    <!-- 左侧菜单栏 -->
    <div class="sidebar-container">
      <Sidebar :items="menuItems" />
    </div>
    <!-- 右侧主要内容 -->
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script>
import Sidebar from '@/components/Sidebar.vue'
export default {
  name: 'AdminLayout',
  components: { Sidebar },
  setup() {
    // 管理员角色菜单项
    const menuItems = [
      { label: '首页',       path: '/admin' },
      { label: '超管管理', path: '/admin/superadmins' },
      { label: '教师管理',   path: '/admin/teachers' },
      { label: '班级管理',   path: '/admin/classes' },
      { label: '课程管理',   path: '/admin/courses' }
    ]
    return { menuItems }
  }
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: calc(100vh - 50px); /* 扣除头部高度，确保无滚动 */
}
.sidebar-container {
  width: 200px;
}
.content {
  flex: 1;
  padding: 20px;
}
</style>
