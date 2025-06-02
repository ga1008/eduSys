<template>
  <div class="dashboard-container">
    <!-- 欢迎信息 -->
    <el-card class="welcome-card">
      <template #header>
        <div class="welcome-header">
          <h2>{{ welcomeMessage }}</h2>
          <el-tag type="success">{{ userStore.user.role === 'teacher' ? '教师' : userStore.user.role }}</el-tag>
        </div>
      </template>
      <div v-if="teacherInfo" class="teacher-info">
        <p><strong>工号：</strong>{{ teacherInfo.teacher_number }}</p>
        <p><strong>邮箱：</strong>{{ teacherInfo.email }}</p>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <div class="stats-container">
      <el-card class="stat-card" shadow="hover" @click="goTo('courses')">
        <div class="stat-content">
          <el-icon size="30" color="#409EFF"><School /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.course_count }}</div>
            <div class="stat-label">教授课程</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover" @click="goTo('students')">
        <div class="stat-content">
          <el-icon size="30" color="#67C23A"><User /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.student_count }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover" @click="goTo('classes')">
        <div class="stat-content">
          <el-icon size="30" color="#E6A23C"><Collection /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.class_count }}</div>
            <div class="stat-label">教学班级</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover" @click="goTo('messages')">
        <div class="stat-content">
          <el-icon size="30" color="#E6A23C"><Message /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.messages || 0 }}</div>
            <div class="stat-label">所有信息</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 当前课程列表 -->
    <el-card class="courses-card">
      <template #header>
        <div class="card-header">
          <h3>{{ showAllCourses ? '全部教学课程' : '当前教学课程' }}</h3>
          <div>
            <el-button v-if="!showAllCourses" type="primary" @click="loadAllCourses" :loading="loadingAllCourses">
              查看全部课程
            </el-button>
            <el-button v-else type="default" @click="showRecentCoursesOnly">
              返回近期课程
            </el-button>
            <el-button
              type="warning"
              @click="$router.push(`/teacher/courses/import`)">
              导入课程
            </el-button>
          </div>

        </div>
      </template>

      <el-table
        :data="currentDisplayCourses"
        v-loading="loading || loadingAllCourses"
        style="width: 100%">
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column label="操作">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="$router.push(`/teacher/courses/students/${scope.row.id}`)">
              学生名单
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="$router.push(`/teacher/courses/homeworks/${scope.row.id}`)">
              作业管理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-container" v-if="showAllCourses">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="allCourses.length"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import { useRouter } from 'vue-router'  // 导入useRouter
import { fetchTeacherDashboard, fetchTeacherCourseClasses } from '@/api/teachers'
import {School, User, Collection, Message} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()  // 获取路由实例
const userStore = useUserStore()
const loading = ref(false)
const teacherInfo = ref(null)
const loadingAllCourses = ref(false)
const welcomeMessage = ref('')
const stats = ref({
  course_count: 0,
  class_count: 0,
  student_count: 0
})
const recentCourses = ref([])
const allCourses = ref([])
const showAllCourses = ref(false)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(10)

// 计算当前显示的课程列表
const currentDisplayCourses = computed(() => {
  if (!showAllCourses.value) {
    return recentCourses.value
  }

  // 分页显示全部课程
  const startIndex = (currentPage.value - 1) * pageSize.value
  return allCourses.value.slice(startIndex, startIndex + pageSize.value)
})

// 分页处理函数
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1 // 重置到第一页
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 加载仪表板数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    const response = await fetchTeacherDashboard()
    teacherInfo.value = response.data.teacher
    stats.value = response.data.stats
    recentCourses.value = response.data.recent_courses

    // 设置欢迎消息
    if (teacherInfo.value && teacherInfo.value.name) {
      welcomeMessage.value = `欢迎回来，${teacherInfo.value.name}！`
    } else {
      welcomeMessage.value = `欢迎回来，${userStore.user.username}！`
    }
  } catch (error) {
    ElMessage.error('加载仪表板数据失败')
    console.error('加载仪表板数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载所有课程
const loadAllCourses = async () => {
  if (allCourses.value.length > 0) {
    // 如果已经加载过，直接显示
    showAllCourses.value = true
    return
  }

  loadingAllCourses.value = true
  try {
    const response = await fetchTeacherCourseClasses()
    allCourses.value = response.data

    showAllCourses.value = true
    currentPage.value = 1 // 重置到第一页
  } catch (error) {
    ElMessage.error('加载全部课程失败')
    console.error('加载全部课程失败:', error)
  } finally {
    loadingAllCourses.value = false
  }
}

// 返回只显示最近课程
const showRecentCoursesOnly = () => {
  showAllCourses.value = false
}

// 点击卡片跳转
const goTo = (route) => {
  router.push(`/teacher/${route}`)
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.teacher-info {
  display: flex;
  gap: 20px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  gap: 15px;
}

.stat-info {
  text-align: left;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.courses-card {
  margin-bottom: 20px;
}
</style>