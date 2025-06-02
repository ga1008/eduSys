<template>
  <div class="course-list">
    <el-row :gutter="20">
      <el-col
        v-for="c in courses"
        :key="c.id"
        :span="6"
        class="mb-4"
      >
        <el-card
          :class="{ active: c.id === selectedId }"
          shadow="hover"
          @click="gotoDetail(c.id)"
        >
          <div class="title">{{ c.name }}</div>
          <div class="meta">
            <span>学分 {{ c.credit }}</span>
            <span>学时 {{ c.hours }}</span>
          </div>
          <div class="teacher" v-if="c.teacher_name">
            任课教师：{{ c.teacher_name }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="!loading && validCourses.length === 0" description="暂无课程" />
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchStudentCourses } from '@/api/student'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const courses = ref([])
const loading = ref(false)
const selectedId = ref(Number(route.query.selected) || null)

const load = async () => {
  loading.value = true
  try {
    const { data } = await fetchStudentCourses()

    if (!data) {
      throw new Error('未获取到课程数据')
    }

    courses.value = Array.isArray(data.results) ? data.results :
                   (Array.isArray(data) ? data : [])
  } catch (error) {
    console.error('加载课程列表失败:', error)
    ElMessage.error('加载课程列表失败')
    courses.value = []
  } finally {
    loading.value = false
  }
}

// 过滤有效的课程数据
const validCourses = computed(() => {
  return courses.value.filter(course =>
    course && typeof course === 'object' && course.id
  ).map(course => ({
    ...course,
    name: course.name || course.course_name || '未命名课程', // 兼容不同API返回格式
    credit: course.credit || '-',
    hours: course.hours || '-'
  }));
})

const gotoDetail = id => {
  router.push({ name: 'StudentCourseDetail', params: { id } })
}

onMounted(load)
</script>

<style scoped>
.course-list {
  padding: 24px;
}
.el-card.active {
  border: 2px solid var(--el-color-primary);
}
.title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 8px;
}
.meta {
  color: #999;
  font-size: 13px;
  margin-bottom: 4px;
}
.teacher {
  font-size: 13px;
  color: #666;
}
</style>
