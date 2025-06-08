import axios from 'axios'
import { useUserStore } from '@/store/user'
import router from '@/router'

const service = axios.create({
  baseURL: '/chat/api', //
  timeout: 8000, //
  withCredentials: true, //
  xsrfCookieName: 'csrftoken',   // axios 自动把 csrftoken → X‑CSRFToken //
  xsrfHeaderName: 'X-CSRFToken' //
})

/* 响应拦截：遇到 401 或 403 自动登出 */ //
service.interceptors.response.use(
  res => res,
  err => {
    // Corrected status code check
    if (err.response && [401, 403].includes(err.response.status)) { //
      useUserStore().logout() //
      router.push('/login') //
    }
    return Promise.reject(err)
  }
)

export default service