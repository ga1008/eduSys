<template>
  <div v-loading="loading" class="student-home-dashboard">
    <el-card shadow="hover" class="dashboard-card welcome-card">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>欢迎回来，{{ studentInfo.name }}同学！</h1>
          <p>班级：{{ studentInfo.className }}</p>
        </div>
        <el-avatar :size="80" :src="studentInfo.avatar || defaultAvatar" icon="UserFilled"/>
      </div>
    </el-card>

    <el-row :gutter="20" class="quick-stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in quickStats" :key="stat.label">
        <el-card shadow="hover" class="dashboard-card stat-item-card">
          <div class="stat-item">
            <el-icon :size="30" class="stat-icon" :color="stat.color">
              <component :is="stat.icon"/>
            </el-icon>
            <div class="stat-details">
              <span class="stat-value">{{ stat.value }}</span>
              <span class="stat-label">{{ stat.label }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :xs="24" :md="14">
        <el-card shadow="hover" class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Memo/></el-icon> 我的任务</span>
              <router-link to="/student/assignments">
                <el-button type="primary" link>查看全部作业</el-button>
              </router-link>
            </div>
          </template>
          <el-empty v-if="!latestAssignments.length" description="太棒了，暂时没有需要处理的作业！"></el-empty>
          <el-scrollbar max-height="400px" v-else>
            <div v-for="assignment in latestAssignments" :key="assignment.id" class="assignment-item">
              <div class="assignment-info">
                <div class="assignment-title-course">
                  <span class="assignment-title">{{ assignment.title }}</span>
                  <el-tag type="info" size="small" effect="plain">{{ assignment.course_name }}</el-tag>
                </div>
                <div class="assignment-deadline">
                  <el-icon>
                    <AlarmClock/>
                  </el-icon>
                  截止：{{ formatDate(assignment.due_date, 'YYYY-MM-DD HH:mm') }}
                  <el-tag :type="getDeadlineTagType(assignment.due_date)" size="small" effect="light" round
                          style="margin-left: 8px;">
                    {{ calculateRemainingTime(assignment.due_date) }}
                  </el-tag>
                </div>
              </div>
              <div class="assignment-actions">
                <el-tag :type="getAssignmentStatusType(assignment)" effect="dark" round class="status-tag">
                  {{ getAssignmentStatusText(assignment) }}
                </el-tag>
                <el-button
                    type="primary"
                    size="small"
                    plain
                    @click="navigateToAssignment(assignment)"
                    :icon="assignment.submitted ? ViewIcon : EditPenIcon"
                >
                  {{ assignment.submitted ? '查看提交' : '去提交' }}
                </el-button>
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="10">
        <el-card shadow="hover" class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Reading/></el-icon> 最近课程</span>
              <router-link to="/student/courses">
                <el-button type="primary" link>所有课程</el-button>
              </router-link>
            </div>
          </template>
          <el-empty v-if="!recentCourses.length" description="暂无最近课程"></el-empty>
          <el-scrollbar max-height="400px" v-else>
            <div v-for="course in recentCourses" :key="course.id" class="course-item">
              <el-icon class="course-icon" :size="24">
                <Notebook/>
              </el-icon>
              <div class="course-details">
                <span class="course-name">{{ course.course_name }}</span>
                <span class="course-teacher">{{ course.teacher_name }}</span>
              </div>
              <el-button type="primary" plain size="small" @click="navigateToCourse(course.id)" :icon="PositionIcon">
                进入课程
              </el-button>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/store/user' //
import {fetchStudentDashboard} from '@/api/student' //
import {ElMessage} from 'element-plus'
import {
  AlarmClock,
  Collection,
  EditPen,
  Files,
  Memo,
  Notebook,
  PieChart,
  Position,
  Reading,
  View
} from '@element-plus/icons-vue' //
import dayjs from 'dayjs' //
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';
const ViewIcon = View;
const EditPenIcon = EditPen;
const PositionIcon = Position;

const router = useRouter() //
const userStore = useUserStore() //
const loading = ref(true)

const studentInfo = ref({
  name: userStore.user?.name || userStore.user?.username || '同学', //
  className: '',
  avatar: userStore.user?.avatar
})

const rawStats = ref({
  course_count: 0,
  pending_assignments: 0,
  avg_score: 0,
  material_count: 0,
  latest_assignments: [],
  recent_courses: []
})

// 快捷统计数据计算属性
const quickStats = computed(() => [
  {label: '在修课程', value: rawStats.value.course_count, icon: Collection, color: '#409EFF'}, //
  {label: '待完成作业', value: rawStats.value.pending_assignments, icon: Memo, color: '#E6A23C'}, //
  {
    label: '平均成绩',
    value: rawStats.value.avg_score !== null && rawStats.value.avg_score !== undefined ? parseFloat(rawStats.value.avg_score).toFixed(1) : 'N/A',
    icon: PieChart,
    color: '#67C23A'
  }, //
  {label: '学习资料', value: rawStats.value.material_count, icon: Files, color: '#F56C6C'} //
])

const latestAssignments = computed(() => rawStats.value.latest_assignments || []) //
const recentCourses = computed(() => rawStats.value.recent_courses || []) //

// 获取仪表盘数据
const fetchDashboardData = async () => {
  loading.value = true
  try {
    const response = await fetchStudentDashboard() //
    rawStats.value = response.data //
    studentInfo.value.name = response.data.name || userStore.user?.username || '同学' //
    studentInfo.value.className = response.data.class_name || '未分配班级' //
  } catch (error) {
    console.error('加载学生首页数据失败:', error)
    ElMessage.error('加载首页数据失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

onMounted(fetchDashboardData)

// 日期格式化
const formatDate = (dateStr, format = 'YYYY-MM-DD') => {
  return dateStr ? dayjs(dateStr).format(format) : 'N/A'
}

// 计算剩余时间
const calculateRemainingTime = (dueDateStr) => {
  const due = dayjs(dueDateStr)
  const now = dayjs()
  if (due.isBefore(now)) {
    return '已截止'
  }
  // fromNow(true) 会移除 '前'/'后' 等，例如 '3 天'
  return due.fromNow(true) + '后'
}

// 获取截止日期标签类型
const getDeadlineTagType = (dueDateStr) => {
  const due = dayjs(dueDateStr);
  const now = dayjs();
  if (due.isBefore(now)) return 'danger'; // 已截止
  if (due.diff(now, 'day') < 3) return 'warning'; // 3天内截止
  return 'success'; // 3天以上
}

// 获取作业状态标签类型
const getAssignmentStatusType = (assignment) => {
  if (assignment.score !== null && assignment.score !== undefined) return 'success' // 已评分
  if (assignment.submitted) return 'primary' // 已提交，未评分 //
  if (dayjs(assignment.due_date).isBefore(dayjs())) return 'danger' // 已逾期 //
  return 'warning' // 待提交
}

// 获取作业状态文本
const getAssignmentStatusText = (assignment) => {
  if (assignment.score !== null && assignment.score !== undefined) return `已评分: ${assignment.score}` //
  if (assignment.submitted) return '已提交' //
  if (dayjs(assignment.due_date).isBefore(dayjs())) return '已逾期' //
  return '待提交'
}

// 跳转到作业提交/详情页面
const navigateToAssignment = (assignment) => {
  // 作业的提交/详情页面路由名称应为 'StudentAssignmentSubmit'，参数为作业ID
  router.push({name: 'StudentAssignmentSubmit', params: {id: assignment.id}})
}

// 跳转到课程详情页面
const navigateToCourse = (teacherCourseClassId) => {
  // 课程详情页路由名称应为 'StudentCourseDetail'，参数为 TeacherCourseClass 的 ID
  router.push({name: 'StudentCourseDetail', params: {id: teacherCourseClassId}})
}

</script>

<style scoped>
.student-home-dashboard {
  padding: 20px;
  background-color: #f4f6f8;
  min-height: calc(100vh - 100px); /* 根据您的布局调整 */
}

.dashboard-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.welcome-card .welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-card .welcome-text h1 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-card .welcome-text p {
  font-size: 14px;
  color: #606266;
}

.quick-stats-row {
  margin-bottom: 0; /* dashboard-card 已有 margin-bottom */
}

.stat-item-card .el-card__body {
  padding: 15px; /* 调整卡片内边距 */
}

.stat-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s ease-in-out;
}

.stat-item:hover {
  transform: translateY(-3px); /* 轻微上浮效果 */
}


.stat-icon {
  margin-right: 15px;
  padding: 10px; /* 给图标一些空间 */
  background-color: var(--el-color-primary-light-9); /* 使用Element Plus主题色 */
  border-radius: 50%; /* 圆形背景 */
}

.stat-details {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.card-header .el-icon {
  margin-right: 6px;
  vertical-align: middle; /* 图标和文字对齐 */
}


.assignment-item, .course-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background-color 0.2s;
}

.assignment-item:last-child, .course-item:last-child {
  border-bottom: none;
}

.assignment-item:hover, .course-item:hover {
  background-color: var(--el-fill-color-light); /* Element Plus 悬浮背景色 */
}


.assignment-info {
  flex-grow: 1;
  margin-right: 15px; /* 与右侧操作按钮间距 */
}

.assignment-title-course {
  margin-bottom: 6px;
}

.assignment-title {
  font-weight: 500;
  color: #303133;
  margin-right: 8px;
}

.assignment-deadline {
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
}

.assignment-deadline .el-icon {
  margin-right: 4px;
}

.assignment-actions {
  display: flex;
  align-items: center;
  gap: 10px; /* 状态标签和按钮之间的间距 */
}

.status-tag {
  min-width: 70px; /* 确保标签有合适的最小宽度 */
  text-align: center;
}

.course-item .course-icon {
  margin-right: 12px;
  color: var(--el-text-color-secondary);
}

.course-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.course-name {
  font-weight: 500;
  color: #303133;
}

.course-teacher {
  font-size: 13px;
  color: #909399;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .welcome-card .welcome-text h1 {
    font-size: 20px;
  }

  .stat-item {
    flex-direction: column; /* 小屏幕上统计项内元素垂直排列 */
    align-items: flex-start;
  }

  .stat-icon {
    margin-bottom: 8px;
  }

  .assignment-item, .course-item {
    flex-direction: column; /* 小屏幕上列表项内元素垂直排列 */
    align-items: flex-start;
  }

  .assignment-actions {
    margin-top: 10px;
    width: 100%; /* 让操作按钮占据整行以便对齐 */
    justify-content: space-between; /* 状态和按钮两端对齐 */
  }

  .course-item .el-button {
    margin-top: 8px;
    width: 100%; /* 课程按钮也占据整行 */
  }
}
</style>