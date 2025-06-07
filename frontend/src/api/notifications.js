import request from '@/utils/request_noti' // 使用我们刚创建的专用请求实例

// ---------- 消息/通知 API ----------

/**
 * 获取通知列表 (收件箱)
 * @param {object} params - 查询参数, e.g., { is_read: false, type: 'private_message' }
 */
export const fetchNotifications = (params) => request.get('/messages/', {params})

/**
 * 获取单条通知详情
 * @param {number} id - 通知ID
 */
export const fetchNotificationById = (id) => request.get(`/messages/${id}/`)

/**
 * 获取未读通知数量
 */
export const fetchUnreadCount = () => request.get('/messages/unread-count/')

/**
 * 发送新消息 (私信)
 * @param {object} data - { recipient: userId, title: '...', content: '...' }
 */
export const sendMessage = (data) => request.post('/messages/', data)

/**
 * 回复消息
 * @param {number} parentId - 被回复的通知ID
 * @param {object} data - { content: '...' }
 */
export const replyToMessage = (parentId, data) => request.post(`/messages/${parentId}/reply/`, data)

/**
 * 将通知标记为已读
 * @param {number} id - 通知ID
 */
export const markAsRead = (id) => request.post(`/messages/${id}/mark-read/`)

/**
 * 将所有通知标记为已读
 */
export const markAllAsRead = () => request.post('/messages/mark-all-as-read/')

/**
 * 删除通知
 * @param {number} id - 通知ID
 */
export const deleteNotification = (id) => request.delete(`/messages/${id}/`)

// ---------- 用户搜索 API ----------

/**
 * 搜索用户以发送消息
 * @param {string} searchTerm - 搜索关键词
 */
export const searchUsers = (searchTerm) => request.get('/search-users/', {params: {search: searchTerm}})


// ---------- 设置与黑名单 API ----------

/**
 * 获取当前用户的通知设置
 */
export const fetchNotificationSettings = () => request.get('/settings/')

/**
 * 更新当前用户的通知设置
 * @param {object} data - 设置对象
 */
export const updateNotificationSettings = (data) => request.put('/settings/', data)

/**
 * 获取黑名单列表
 */
export const fetchBlockedContacts = () => request.get('/blocked-contacts/')

/**
 * 添加用户到黑名单
 * @param {number} userId - 要拉黑的用户ID
 */
export const blockContact = (userId) => request.post('/blocked-contacts/', {blocked_user: userId})

/**
 * 从黑名单移除用户
 * @param {number} blockId - 黑名单记录的ID
 */
export const unblockContact = (blockId) => request.delete(`/blocked-contacts/${blockId}/`)

/**
 * 获取已发送的消息列表
 * @param {object} params - 查询参数, e.g., { search: '关键词' }
 */
export const fetchSentNotifications = (params) => request.get('/messages/sent/', {params})

/**
 * 撤回消息
 * @param {number} id - 通知ID
 */
export const retractMessage = (id) => request.post(`/messages/${id}/retract/`)