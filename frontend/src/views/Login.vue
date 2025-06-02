<template>
  <div class="login-wrapper">
    <el-card class="login-card">
      <h2>{{ pageTitle }}</h2>

      <el-form @keyup.enter="handleLogin">
        <!-- 用户名 -->
        <el-form-item>
          <el-input v-model="username" placeholder="用户名" />
        </el-form-item>

        <!-- 密码 -->
        <el-form-item>
          <el-input v-model="password" type="password" placeholder="密码" />
        </el-form-item>

        <!-- 角色选择 (仅在没有预设角色时显示) -->
        <el-form-item v-if="!props.presetRole">
          <el-select v-model="selectedRole" placeholder="请选择角色" style="width: 100%">
            <el-option label="超级管理员" value="admin" />
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  presetRole: String,
  title: {
    type: String,
    default: '系统登录'
  }
})

const username = ref('')
const password = ref('')
// selectedRole 用于 v-if="!props.presetRole" 时的选择器
const selectedRole = ref(props.presetRole || '')
const loading = ref(false)
const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => {
  if (props.presetRole === 'student') return '学生登录'
  if (props.presetRole === 'teacher') return '教师登录'
  if (props.presetRole === 'admin') return '管理员登录'
  return props.title // 如果有 props.title 且无 presetRole，则使用它，否则是默认的 "系统登录"
})

// 确保 selectedRole 在组件挂载时正确反映 presetRole
onMounted(() => {
  if (props.presetRole) {
    selectedRole.value = props.presetRole
  }
})

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  // 如果角色选择框可见 (即没有预设角色)，则校验角色是否已选择
  if (!props.presetRole && !selectedRole.value) {
    ElMessage.warning('请选择角色')
    return
  }

  loading.value = true
  try {
    await userStore.login({
      username: username.value,
      password: password.value,
      role: selectedRole.value // 使用 selectedRole，它会是 presetRole 或用户选择的值
    })
    // 登录成功后，userStore.user 和 userStore.routesInjected 会被更新
    // beforeEach 会处理重定向，但为了更直接的用户体验，可以主动跳转
    const redirect = route.query.redirect
    if (redirect && typeof redirect === 'string') {
      router.push(redirect)
    } else {
      // 根据角色跳转到默认首页
      if (userStore.user.role === 'teacher') router.push('/teacher/dashboard')
      else if (userStore.user.role === 'student') router.push('/student/assignments')
      else if (userStore.user.role === 'admin') router.push('/admin')
      else router.push('/') // 后备，理论上不会到这里
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 50px);
  background: #f0f2f5;
}
.login-card {
  width: 320px;
}
</style>