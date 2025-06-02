<template>
  <HeaderBar />
  <!-- 全局骨架 / 进度条 -->
  <!-- v-loading 指令 + 全屏遮罩 + 锁定滚动 -->
  <div v-loading.fullscreen.lock="loading">
    <Suspense @pending="loading = true" @resolve="loading = false">
      <template #default>
        <router-view />
      </template>

      <!-- fallback 可选 -->
      <template #fallback>
        <div class="h-screen flex items-center justify-center text-gray-400">
          页面加载中…
        </div>
      </template>
    </Suspense>
  </div>
</template>

<script>
import HeaderBar from '@/components/HeaderBar.vue'
import { ref } from 'vue'
const loading = ref(false)
export default {
  name: 'App',
  components: {
    HeaderBar
  }
}
</script>

<style>
/* 全局样式：去除默认边距等，可根据需要调整 */
body {
  margin: 0;
  font-family: Arial, sans-serif;
}
</style>
