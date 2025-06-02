<template>
  <div class="header-bar">
    <div class="logo">{{ title }}</div>
    <div class="spacer"></div>
    <!-- 登录用户信息和退出按钮 -->
    <div v-if="user" class="user-info">
      {{ user.name }}
      <span @click="handleLogout" class="logout">退出</span>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'

export default {
  name: 'HeaderBar',
  setup() {
    const userStore = useUserStore()
    // 读取当前用户信息
    const user = computed(() => userStore.user)
    const title = '在线教育平台'
    // 退出登录方法
    const logout = () => {
      userStore.logout()
    }
    const handleLogout = () => {
      ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
        .then(() => logout())
        .catch(() => {}) // 取消
    }
    return { user, title, logout, handleLogout }
  }
}
</script>

<style scoped>
.header-bar {
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 50px;
  background-color: #409EFF; /* Element Plus 默认主题色 */
  color: #fff;
}
.logo {
  font-size: 18px;
  font-weight: bold;
}
.spacer {
  flex: 1;
}
.user-info {
  font-size: 14px;
}
.logout {
  margin-left: 10px;
  cursor: pointer;
  text-decoration: underline;
}
.logout:hover {
  opacity: 0.8;
}
</style>