import {defineStore} from 'pinia'
import {fetchUnreadCount} from '@/api/notifications'

export const useNotificationStore = defineStore('notification', {
    state: () => ({
        unreadCount: 0,
        // 定时器ID
        intervalId: null
    }),
    actions: {
        // 从API获取未读消息数并更新state
        async updateUnreadCount() {
            try {
                const response = await fetchUnreadCount()
                this.unreadCount = response.data.unread_count
            } catch (error) {
                console.error('获取未读消息数失败:', error)
                this.unreadCount = 0
            }
        },
        // 启动定时轮询
        startPolling() {
            // 先立即执行一次
            this.updateUnreadCount()
            // 如果已经有定时器在运行，先清除
            if (this.intervalId) {
                clearInterval(this.intervalId)
            }
            // 设置每分钟轮询一次
            this.intervalId = setInterval(() => {
                this.updateUnreadCount()
            }, 60 * 1000) // 60秒
        },
        // 停止轮询
        stopPolling() {
            if (this.intervalId) {
                clearInterval(this.intervalId)
                this.intervalId = null
                this.unreadCount = 0 // 重置
            }
        }
    }
})