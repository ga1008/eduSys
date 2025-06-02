<!--学生个人仪表台-->
<!-- frontend/src/views/student/Dashboard.vue -->
<template>
  <div class="dashboard-container">
    <!-- 欢迎信息 -->
    <el-card class="welcome-card">
      <template #header>
        <div class="welcome-header">
          <h2>{{ welcomeMessage }}</h2>
          <el-tag type="success">学生</el-tag>
        </div>
      </template>
      <div v-if="studentInfo" class="student-info">
        <p><strong>学号：</strong>{{ studentInfo.student_number }}</p>
        <p><strong>班级：</strong>{{ studentInfo.class_name }}</p>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <div class="stats-container">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon size="30" color="#409EFF"><Notebook /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.course_count }}</div>
            <div class="stat-label">在修课程</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon size="30" color="#67C23A"><Document /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.pending_assignments }}</div>
            <div class="stat-label">待完成作业</div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <el-icon size="30" color="#E6A23C"><Trophy /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ stats.avg_score || 'N/A' }}</div>
            <div class="stat-label">平均成绩</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 课程列表 -->
    <el-card class="courses-card">
      <template #header>
        <div class="card-header">
          <h3>{{ showAllCourses ? '全部课程' : '当前学期课程' }}</h3>
          <div>
            <el-button
              v-if="!showAllCourses"
              type="primary"
              @click="loadAllCourses"
              :loading="loadingAllCourses">
              查看历史课程
            </el-button>
            <el-button v-else type="default" @click="showRecentCoursesOnly">
              返回当前学期
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="currentDisplayCourses"
        v-loading="loading"
        style="width: 100%">
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="teacher_name" label="授课教师" />
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="$router.push(`/student/courses/${scope.row.id}/assignments/`)">
              作业列表
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="$router.push(`/student/courses/${scope.row.id}`)">
              课程详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="showAllCourses">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20]"
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
import { fetchStudentDashboard, fetchStudentCourses } from '@/api/student'
import { Notebook, Document, Trophy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const studentInfo = ref(null)
const loadingAllCourses = ref(false)
const welcomeMessage = ref('')
const stats = ref({
  course_count: 0,
  pending_assignments: 0,
  avg_score: null
})
const recentCourses = ref([])
const allCourses = ref([])
const showAllCourses = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(10)

const currentDisplayCourses = computed(() => {
  return showAllCourses.value
    ? allCourses.value.slice((currentPage.value - 1) * pageSize.value, currentPage.value * pageSize.value)
    : recentCourses.value
})

const loadDashboardData = async () => {
  loading.value = true
  try {
    const response = await fetchStudentDashboard()
    studentInfo.value = response.data.student
    stats.value = response.data.stats
    recentCourses.value = response.data.recent_courses

    welcomeMessage.value = `欢迎回来，${studentInfo.value.name || userStore.user.username}！`
  } catch (error) {
    ElMessage.error('加载数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadAllCourses = async () => {
  if (allCourses.value.length > 0) {
    showAllCourses.value = true
    return
  }

  loadingAllCourses.value = true
  try {
    const response = await fetchStudentCourses()
    allCourses.value = response.data
    showAllCourses.value = true
  } catch (error) {
    ElMessage.error('加载课程失败')
  } finally {
    loadingAllCourses.value = false
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const showRecentCoursesOnly = () => {
  showAllCourses.value = false
}

onMounted(loadDashboardData)
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card .stat-content {
  display: flex;
  align-items: center;
  padding: 20px;
  gap: 15px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
}
</style>
