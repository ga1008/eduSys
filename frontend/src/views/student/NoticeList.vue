<!--通知公告-->
<template>
  <div class="notice-list">
    <div class="notice-list-header">
      <h2>通知公告</h2>
    </div>
    <div class="notice-list-content">
      <ul>
        <li v-for="(notice, index) in notices" :key="index">
          <h3>{{ notice.title }}</h3>
          <p>{{ notice.content }}</p>
          <span>{{ notice.date }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
<script>
import { ref, onMounted } from 'vue'
import { fetchStudentNotices } from '@/api/student' // 假设你有一个API模块来获取通知数据
export default {
  name: 'NoticeList',
  setup() {
    const notices = ref([])

    onMounted(async () => {
      try {
        const response = await fetchStudentNotices()
        notices.value = response.data
      } catch (error) {
        console.error('获取通知失败:', error)
      }
    })

    return {
      notices
    }
  }
}
</script>
<style scoped>
.notice-list {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}
.notice-list-header {
  margin-bottom: 20px;
}
.notice-list-header h2 {
  font-size: 24px;
  color: #333;
}
.notice-list-content ul {
  list-style: none;
  padding: 0;
}
.notice-list-content li {
  background-color: #fff;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.notice-list-content li h3 {
  font-size: 18px;
  color: #333;
}
.notice-list-content li p {
  font-size: 14px;
  color: #666;
}
.notice-list-content li span {
  font-size: 12px;
  color: #999;
}

</style>