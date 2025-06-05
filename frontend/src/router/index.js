import {createRouter, createWebHistory} from 'vue-router'
import Login from '@/views/Login.vue' // 通用登录组件
import {useUserStore} from '@/store/user' //
import teacherRoutes from './teacher.routes' // 教师路由是静态导入的
import {ElMessage} from 'element-plus' // 引入 ElMessage

// adminRoutes 和 studentRoutes 将由 userStore 动态添加

const staticRoutes = [
    {path: '/', redirect: '/login/student'}, // 默认重定向到学生登录
    {path: '/login', redirect: '/login/student'}, // /login 也重定向到学生登录

    // 分离的登录入口
    {
        path: '/login/student',
        name: 'StudentLogin',
        component: Login,
        props: {presetRole: 'student', title: '学生登录'}, //
        meta: {public: true} //
    },
    {
        path: '/login/teacher',
        name: 'TeacherLogin',
        component: Login,
        props: {presetRole: 'teacher', title: '教师登录'}, //
        meta: {public: true} //
    },
    {
        path: '/login/admin',
        name: 'AdminLogin',
        component: Login,
        props: {presetRole: 'admin', title: '管理员登录'}, //
        meta: {public: true} //
    },

    ...teacherRoutes //
]

const router = createRouter({
    history: createWebHistory(),
    routes: staticRoutes
})

/* ========= 全局守卫 ========= */
router.beforeEach(async (to, from, next) => {
    const userStore = useUserStore() //

    // 确保用户信息和路由已加载
    // 如果用户未登录（store中没有用户信息），尝试恢复会话
    // userStore.restore() 会尝试获取用户信息并调用 _injectRoutes(true)
    if (!userStore.user && localStorage.getItem('user')) { // 检查localStorage，以便在Pinia store重置后恢复
        await userStore.restore(); // restore会尝试从localStorage恢复，然后从后端获取，并注入路由
    } else if (userStore.user && !userStore._routesInjected) {
        // 如果用户已存在（例如页面刷新后从localStorage恢复），但路由未注入
        await userStore._injectRoutes(true); //
    }


    const loggedIn = !!userStore.user // 重新检查登录状态
    const targetRole = to.meta.role //
    const isLoginPage = to.name === 'StudentLogin' || to.name === 'TeacherLogin' || to.name === 'AdminLogin' //

    // 1. 处理公共路径 (如登录页)
    if (to.meta.public) { //
        if (loggedIn && isLoginPage) {
            // 已登录用户尝试访问登录页，重定向到其角色首页
            // *** 修改学生重定向路径 ***
            const homePath = userStore.user.role === 'teacher' ? '/teacher/dashboard' :
                userStore.user.role === 'student' ? '/student' : // 修改为 /student (新的学生主页)
                    userStore.user.role === 'admin' ? '/admin' : `/${userStore.user.role}` // 后备
            return next(homePath)
        }
        return next() // 公共路径，非登录页或未登录，正常访问
    }

    // 2. 处理受保护路径 (meta.public 不为 true)
    if (!loggedIn) {
        // 未登录，重定向到对应的登录页
        let loginRouteName = 'StudentLogin' // 默认学生登录
        if (to.path.startsWith('/teacher') || targetRole === 'teacher') { //
            loginRouteName = 'TeacherLogin' //
        } else if (to.path.startsWith('/admin') || targetRole === 'admin') { //
            loginRouteName = 'AdminLogin' //
        }
        return next({name: loginRouteName, query: {redirect: to.fullPath}}) //
    }

    // 3. 已登录，访问受保护路径
    // 检查角色权限
    if (targetRole && targetRole !== userStore.user.role) { //
        ElMessage.error('您没有权限访问此页面') //
        // 重定向到用户各自的首页
        // *** 修改学生重定向路径 ***
        const homePath = userStore.user.role === 'teacher' ? '/teacher/dashboard' :
            userStore.user.role === 'student' ? '/student' : // 修改为 /student
                userStore.user.role === 'admin' ? '/admin' : `/${userStore.user.role}` //
        return next(homePath)
    }

    // 4. 解决动态路由添加后首次导航无法匹配的问题
    // (Vue Router 4.x 通常不需要这个，但如果遇到问题可以保留)
    // 确保 to.name 存在，表示路由定义是有效的，并且不是正要去的登录页本身
    // to.matched.length === 0 可能表示路由还未完全准备好
    if (to.matched.length === 0 && to.name && !isLoginPage && userStore._routesInjected) { //
        // 确保路由已注入再尝试 next({ ...to, replace: true })
        // 避免在路由注入完成前无限循环
        return next({...to, replace: true}) //
    }

    next()
})

export default router