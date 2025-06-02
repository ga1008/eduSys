import { defineStore } from 'pinia'
import { login as loginApi, fetchMe, logout as logoutApi } from '@/api/auth'
import router from '@/router'
import adminRoutes from '@/router/admin.routes'
// import teacherRoutes from '@/router/teacher.routes'; // 教师路由是静态的，不再由此处动态添加
import studentRoutes from '@/router/student.routes'

/* 把后端各种超管标识统一映射成 'admin' */
const ROLE_MAP = {
  admin: 'admin',
  superadmin: 'admin',
  super_admin: 'admin',
  administrator: 'admin',
  teacher: 'teacher',
  student: 'student'
}

export const useUserStore = defineStore('user', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    _routesInjected: false
  }),

  getters: {
    role: s => s.user?.role
  },

  actions: {
    /* 登录 */
    async login({ username, password, role }) {
      await loginApi(username, password, role)
      await this._fetchAndSetUser()
      await this._injectRoutes(true)
      // 重定向逻辑已移至 Login.vue 或由 router.beforeEach 处理
      // router.replace({ path: `/${this.role}` }) // 旧的重定向逻辑，已移除
    },

    /* 退出登录 */
    async logout() {
      try {
        await logoutApi()
      } catch (_) {
        /* 网络异常时也继续做前端清理 */
      }

      // 清理特定角色的动态路由
      if (this.user) {
        if (this.user.role === 'admin') {
          adminRoutes.forEach(route => {
            if (router.hasRoute(route.name)) router.removeRoute(route.name);
          });
        } else if (this.user.role === 'student') {
          studentRoutes.forEach(route => {
            if (router.hasRoute(route.name)) router.removeRoute(route.name);
          });
        }
        // 教师路由是静态的，不需要在这里移除
      }

      this.user = null
      this._routesInjected = false
      localStorage.removeItem('user')
      router.replace('/login/student') // 登出后重定向到学生登录页
      this.$reset()
    },

    /* 刷新时恢复 session */
    async restore() {
      try {
        // 如果没有用户信息，尝试从后端获取
        if (!this.user && localStorage.getItem('user')) { // 检查 localStorage 中是否有 user
             this.user = JSON.parse(localStorage.getItem('user')); // 尝试从 localStorage 恢复
        }
        if (!this.user) { // 如果 localStorage 中也没有，或解析失败，则尝试从后端获取
          await this._fetchAndSetUser()
        }


        // 关键：无论之前是否注入过路由，刷新页面后都重新注入
        if (this.user) {
          await this._injectRoutes(true) // 使用 force: true 确保路由被注入
          return true
        }
      } catch (e) {
        console.error('恢复用户会话失败', e)
        // 清理工作，防止无效状态
        this.user = null
        this._routesInjected = false
        localStorage.removeItem('user')
      }
      return false
    },

    /* 私有方法：获取并设置用户信息 */
    async _fetchAndSetUser() {
      const { data } = await fetchMe()
      if (!data || !data.role) {
        throw new Error('获取用户信息失败或角色信息缺失')
      }

      // 统一角色处理（转小写再匹配）
      const role = (data.role || '').toLowerCase()
      const normalizedRole = ROLE_MAP[role] || role // 如果映射不到，则使用原始角色（小写）

      if (!['admin', 'teacher', 'student'].includes(normalizedRole)) {
        console.warn(`未知的用户角色: ${data.role}, 标准化后为: ${normalizedRole}. 将可能导致路由问题.`)
        // 可以选择抛出错误，或者赋予一个默认角色/权限不足的状态
      }

      this.user = { ...data, role: normalizedRole }
      localStorage.setItem('user', JSON.stringify(this.user))
    },

    /* 私有方法：注入角色对应的路由 */
    async _injectRoutes(force = false) {
      if (!force && this._routesInjected) return
      if (!this.user || !this.user.role) {
        console.error('无法注入路由：用户信息或角色缺失')
        return
      }

      // 清理先前可能已注入的动态路由 (admin, student)
      // 这样做是为了处理角色切换或强制刷新路由的场景
      adminRoutes.forEach(route => {
        if (router.hasRoute(route.name)) {
          router.removeRoute(route.name)
        }
      })
      studentRoutes.forEach(route => {
        if (router.hasRoute(route.name)) {
          router.removeRoute(route.name)
        }
      })
      // 教师路由是静态的，不在此处管理

      let routesToAdd = []
      if (this.user.role === 'admin') {
        routesToAdd = adminRoutes
      } else if (this.user.role === 'student') {
        routesToAdd = studentRoutes
      }
      // 教师角色不在此处添加动态路由

      if (!routesToAdd.length && (this.user.role === 'admin' || this.user.role === 'student')) {
        console.warn(`没有找到角色 '${this.user.role}' 对应的路由配置，但期望有。`)
      }

      routesToAdd.forEach(route => {
        if (!router.hasRoute(route.name)) { // 避免重复添加同名路由，尽管 addRoute 通常能处理
          router.addRoute(route)
        }
      })

      // 仅当确实为 admin 或 student 添加了路由，或角色是 teacher (静态路由已存在) 时，才标记为 injected
      if (this.user.role === 'admin' || this.user.role === 'student' || this.user.role === 'teacher') {
         this._routesInjected = true
      } else {
         this._routesInjected = false // 对于未知或无动态路由的角色
         console.warn(`角色 ${this.user.role} 没有配置动态路由，routesInjected 状态未改变或设为 false`)
      }
    }
  }
})