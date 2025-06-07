import axios from 'axios'
import {useUserStore} from '@/store/user'
import router from '@/router'
import {ElMessage} from 'element-plus'

const notificationService = axios.create({
    baseURL: '/notifications/api', // 指向新的后端通知应用API
    timeout: 10000,
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken'
})

// 响应拦截器
notificationService.interceptors.response.use(
    res => res,
    err => {
        // 处理401未授权，自动登出
        if (err.response?.status === 401) {
            useUserStore().logout()
            router.push('/login')
            ElMessage.error('登录状态已过期，请重新登录')
        } else if (err.response?.data?.detail) {
            // 显示后端返回的具体错误信息
            ElMessage.error(err.response.data.detail)
        } else {
            ElMessage.error('操作失败，请稍后再试')
        }
        return Promise.reject(err)
    }
)

export default notificationService