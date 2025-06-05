<template>
  <div class="student-layout">
    <div class="sidebar-container">
      <Sidebar :items="menuItems" />
    </div>
    <div class="content">
      <router-view />
    </div>
  </div>
</template>

<script>
import Sidebar from '@/components/Sidebar.vue'
export default {
  name: 'StudentLayout',
  components: { Sidebar },
  setup() {
    const menuItems = [
      { label: '首页', path: '/student' },
      { label: '我的课程', path: '/student/courses' },
      // { label: '课程资源', path: '/student/courses/materials' },
      { label: '我的作业', path: '/student/assignments' },
      // { label: '在线工具', path: '/student/tools' },
      // { label: '在线论坛', path: '/student/forum' },
    ]
    return { menuItems }
  }
}
</script>

<style scoped>
.student-layout {
  display: flex;
  min-height: calc(100vh - 50px);
}
.sidebar-container {
  width: 200px;
}
.content {
  flex: 1;
  padding: 20px;
}
</style>
