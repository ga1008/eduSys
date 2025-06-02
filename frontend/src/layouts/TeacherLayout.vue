<template>
  <div class="teacher-layout">
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
  name: 'TeacherLayout',
  components: {
    Sidebar
  },
  setup() {
    // 教师角色菜单项
    const menuItems = [
      { label: '教师首页', path: '/teacher/dashboard' },
      { label: '我的课程', path: '/teacher/courses' },
      { label: '我的学生', path: '/teacher/students' },
      { label: '作业管理', path: '/teacher/courses/homeworks' },
    ]
    return { menuItems }
  }
}
</script>

<style scoped>
.teacher-layout {
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