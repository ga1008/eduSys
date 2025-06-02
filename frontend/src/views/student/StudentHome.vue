<template>
  <div class="student-home">
    <!-- 欢迎信息 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <div class="welcome-content">
            <div>
              <h2>欢迎回来，{{ userInfo.name }}！</h2>
              <p class="sub-info">{{ currentClass }}</p>
            </div>
            <el-avatar :size="60" :src="userInfo.avatar"/>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据概览 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xl="6" :lg="8" :md="12" :sm="24">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#409EFF">
              <Collection/>
            </el-icon>
            <div class="stat-text">
              <div class="stat-value">{{ stats.course_count }}</div>
              <div class="stat-label">在修课程</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xl="6" :lg="8" :md="12" :sm="24">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#67C23A">
              <Document/>
            </el-icon>
            <div class="stat-text">
              <div class="stat-value">{{ stats.pending_assignments }}</div>
              <div class="stat-label">待完成作业</div>
            </div>
          </div>
        </el-card>
      </el-col>
<!--      <el-col :xl="6" :lg="8" :md="12" :sm="24">-->
<!--        <el-card class="stat-card">-->
<!--          <div class="stat-content">-->
<!--            <el-icon class="stat-icon" color="#E6A23C">-->
<!--              <Clock/>-->
<!--            </el-icon>-->
<!--            <div class="stat-text">-->
<!--              <div class="stat-value">{{ stats.expired_count }}</div>-->
<!--              <div class="stat-label">即将截止</div>-->
<!--            </div>-->
<!--          </div>-->
<!--        </el-card>-->
<!--      </el-col>-->
      <el-col :xl="6" :lg="8" :md="12" :sm="24">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C">
              <Download/>
            </el-icon>
            <div class="stat-text">
              <div class="stat-value">{{ stats.material_count }}</div>
              <div class="stat-label">新资源</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xl="6" :lg="8" :md="12" :sm="24">
        <el-card class="stat-card">
          <div class="stat-content">
            <el-icon class="stat-icon" color="#F56C6C">
              <Message/>
            </el-icon>
            <div class="stat-text">
              <div class="stat-value">{{ stats.material_count }}</div>
              <div class="stat-label">新消息</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最新动态 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="latest-card">
          <template #header>
            <div class="card-header">
              <h3>最近作业</h3>
              <router-link to="/student/courses">
                <el-button type="text">查看全部</el-button>
              </router-link>
            </div>
          </template>
          <el-table :data="latestAssignments" style="width: 100%">
            <el-table-column prop="title" label="作业名称"/>
            <el-table-column label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="getStatusType(row)" size="small">
                  {{ getStatusText(row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="发布时间" width="120">
              <template #default="{row}">
                {{ formatDate(row.update_time) }}

                <el-tag :type="success" size="small">
                  {{ formatTime(row.update_time) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="截止时间" width="120">
              <template #default="{row}">
                {{ formatDate(row.due_date) }}

                <el-tag :type="getDueDatetimeStatusType(row.due_date)" size="small">
                  {{ formatTime(row.due_date) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="latest-card">
          <template #header>
            <div class="card-header">
              <h3>最新公告</h3>
              <router-link to="/student/notices">
                <el-button type="text">查看全部</el-button>
              </router-link>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
                v-for="notice in latestNotices"
                :key="notice.id"
                :timestamp="formatDate(notice.publish_time)"
                placement="top"
            >
              <el-card shadow="hover">
                <h4>{{ notice.title }}</h4>
                <p class="notice-content">{{ notice.content }}</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {Message, Collection, Document, Download} from '@element-plus/icons-vue'
import {useUserStore} from '@/store/user'
import {ElMessage} from "element-plus";
import {fetchStudentDashboard} from '@/api/student'

const userStore = useUserStore()
const loading = ref(false)

// 用户信息
const userInfo = ref({
  name: userStore.user.name || '同学',
  avatar: userStore.user.avatar || ''
})

// 统计数据
const stats = ref({
  course_count: 0,
  pending_assignments: 0,
  expired_count: 0,
  material_count: 0
})

const currentClass = ref('')
const latestAssignments = ref([])
const latestNotices = ref([])

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString()
}

const formatTime = (dateStr) => {
  return new Date(dateStr).toLocaleTimeString()
}

const getStatusType = (assignment) => {
  if (assignment.submitted) return 'success'
  if (new Date(assignment.due_date) < new Date()) return 'danger'
  return 'warning'
}

const getDueDatetimeStatusType = (dueDate) => {
  const due_date_day = new Date(dueDate).getDay()
  const now_day = new Date().getDay()
  if (due_date_day > now_day) return 'success'

  const due_date_time = new Date(dueDate).getTime()
  const now_time = new Date().getTime()
  if (due_date_time > now_time) return 'warning'
  return 'danger'
}

const getStatusText = (assignment) => {
  if (assignment.submitted) return '已提交'
  if (new Date(assignment.due_date) < new Date()) return '已过期'
  return '待提交'
}

const fetchDashboardData = async () => {
  try {
    loading.value = true
    const response = await fetchStudentDashboard()
    stats.value = response.data

    userInfo.value.name = response.data.name || userStore.user.username
    currentClass.value = response.data.class_name || '未分班'
    latestAssignments.value = response.data.latest_assignments
    latestNotices.value = response.data.latest_notices
  } catch (error) {
    ElMessage.error(' StudentHome 加载数据失败 ' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboardData)
</script>

<style scoped>
.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sub-info {
  color: #909399;
  margin-top: 8px;
}

.stats-row {
  margin: 20px 0;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  font-size: 40px;
  margin-right: 20px;
}

.stat-text {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  color: #909399;
}

.latest-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notice-content {
  color: #606266;
  margin-top: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>