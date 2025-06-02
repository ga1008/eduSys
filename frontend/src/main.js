// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import { useUserStore } from '@/store/user'   // ★ 需要在 pinia 注册后再用

/* ---------------- bootstrap ---------------- */
async function bootstrap () {
  // 1. 创建 app & pinia
  const app   = createApp(App)
  const pinia = createPinia()
  app.use(pinia)

  // 2. 尝试恢复会话并注入动态路由
  const userStore = useUserStore()
  await userStore.restore()      // restore() 内部已做路由注入

  // 3. 再挂载 Router、ElementPlus
  app.use(router)
  app.use(ElementPlus, { locale: zhCn })

  // 4. 最后挂载到 DOM
  await router.isReady()
  app.mount('#app')
}

bootstrap()
