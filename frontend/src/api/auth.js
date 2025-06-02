import request from '@/utils/request'

/* 登录：把用户名、密码、角色发给后端 */
export const login = (username, password, role) =>
  request.post('/login/', { username, password, role })

/* 获取当前用户信息（角色、姓名等） */
export const fetchMe = () => request.get('/me/')
/* 退出登录 */
export const logout = () => request.post('/logout/')