<template>
  <div class="course-detail" v-loading="loading">
    <el-card v-if="course">
      <template #header>
        <div class="header">
          <span>{{ course.name }}</span>
          <el-tag type="success" effect="plain">{{ course.credit }} 学分</el-tag>
          <el-tag type="info" effect="plain">{{ course.hours }} 学时</el-tag>
        </div>
      </template>

      <p v-if="course.description">{{ course.description }}</p>

      <el-descriptions :column="1" border class="mt-2">
        <el-descriptions-item label="任课教师">{{ course.teacher_name || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="教材" v-if="course.textbook">{{ course.textbook }}</el-descriptions-item>
        <el-descriptions-item label="教学大纲" v-if="course.syllabus">{{ course.syllabus }}</el-descriptions-item>
        <el-descriptions-item label="当前进度" v-if="course.progress">{{ course.progress }}</el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <!-- 继续扩展：作业 / 资料等 Tab -->
      <router-view /> <!-- 保持原有嵌套路由 -->
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchStudentCourseDetail } from '@/api/student'

const route = useRoute()
const router = useRouter()

const course = ref(null)
const loading = ref(false)

const load = async () => {
  const id = route.params.id
  if (!id) {
    // 未带 id 直接回列表
    router.replace({ name: 'StudentCourses' })
    return
  }
  loading.value = true
  try {
    const { data } = await fetchStudentCourseDetail(id)
    course.value = data
  } catch (e) {
    ElMessage.error('课程不存在或已下架')
    router.replace({ name: 'StudentCourses' })
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.course-detail {
  padding: 24px;
}
.header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}
</style>
