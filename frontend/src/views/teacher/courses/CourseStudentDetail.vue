<template>
  <div class="student-detail">
    <div class="header-container">
      <h2>学生详情</h2>
      <el-button @click="goBack" type="primary" plain>返回</el-button>
    </div>

    <div v-loading="loading">
      <el-row :gutter="20">
        <!-- 基本信息 -->
        <el-col :span="12">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>基本信息</span>
                <el-tag size="small" type="success">在校</el-tag>
              </div>
            </template>
            <el-descriptions direction="vertical" :column="1" border>
              <el-descriptions-item label="姓名">
                {{ studentData.student?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="学号">
                {{ studentData.student?.student_number }}
              </el-descriptions-item>
              <el-descriptions-item label="邮箱">
                {{ studentData.student?.email || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="最近登录">
                {{ formatDate(studentData.student?.last_login) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <!-- 教育背景 -->
        <el-col :span="12">
          <el-card class="edu-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>教育背景</span>
              </div>
            </template>
            <el-descriptions direction="vertical" :column="1" border>
              <el-descriptions-item label="班级">
                <el-tag>{{ studentData.education?.class_name }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="专业">
                {{ studentData.education?.major }}
              </el-descriptions-item>
              <el-descriptions-item label="学院">
                {{ studentData.education?.department }}
              </el-descriptions-item>
              <el-descriptions-item label="年级">
                {{ studentData.education?.grade }}级
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 学习活动 -->
      <el-card class="activity-card" shadow="hover" style="margin-top: 20px">
        <template #header>
          <div class="card-header">
            <span>学习活动</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="12">
            <h4>作业提交统计</h4>
            <el-progress
              :percentage="getSubmissionPercentage"
              :format="format"
              status="success"
            ></el-progress>
            <div class="stats-container">
              <div class="stat-item">
                <div class="stat-value">{{ studentData.activities?.submissions_stats?.total || 0 }}</div>
                <div class="stat-label">总提交数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ studentData.activities?.submissions_stats?.graded || 0 }}</div>
                <div class="stat-label">已批改</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">
                  {{ formatScore(studentData.activities?.submissions_stats?.avg_score) }}
                </div>
                <div class="stat-label">平均分</div>
              </div>
            </div>
          </el-col>

          <el-col :span="12">
            <h4>最近提交</h4>
            <div v-if="studentData.activities?.last_submission">
              <el-card shadow="never" class="last-submission">
                <h5>{{ studentData.activities.last_submission.assignment_title }}</h5>
                <p>
                  提交时间: {{ formatDateTime(studentData.activities.last_submission.submit_time) }}
                </p>
                <p v-if="studentData.activities.last_submission.score !== null">
                  得分:
                  <el-tag type="success">{{ studentData.activities.last_submission.score }}</el-tag>
                </p>
                <p v-else-if="studentData.activities.last_submission.is_returned">
                  状态: <el-tag type="warning">被退回</el-tag>
                </p>
                <p v-else>
                  状态: <el-tag type="info">待批改</el-tag>
                </p>
              </el-card>
            </div>
            <el-empty v-else description="暂无提交记录"></el-empty>
          </el-col>
        </el-row>
      </el-card>

      <!-- 其他信息 -->
      <el-card class="other-card" shadow="hover" style="margin-top: 20px">
        <template #header>
          <div class="card-header">
            <span>课程参与情况</span>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="8">
            <div class="other-item">
              <h4>出勤情况</h4>
              <el-tag type="success">{{attendanceStatus}}</el-tag>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="other-item">
              <h4>课堂表现</h4>
              <el-rate v-model="classPerformance" disabled></el-rate>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="other-item">
              <h4>资料下载次数</h4>
              <div class="download-count">{{dataDownloadCount}}</div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import couRequest from '@/utils/request_cou'

const router = useRouter();
const route = useRoute();
const courseClassId = computed(() => route.params.courseClassId);
const studentId = computed(() => route.params.studentId);
const loading = ref(true);
const studentData = ref({});

// 示例数据 - 实际应从API获取
const classPerformance = ref(0);
const dataDownloadCount = ref(0);
const attendanceStatus = ref('良好'); // 示例数据

// 获取学生详情
const fetchStudentDetail = async () => {
  loading.value = true;
  try {
    const response = await couRequest.get(
      `/teacher-course-classes/${courseClassId.value}/students/${studentId.value}/`
    );
    studentData.value = response.data;
  } catch (error) {
    ElMessage.error('获取学生详情失败：' + (error.response?.data?.detail || '未知错误'));
  } finally {
    loading.value = false;
  }
};

// 计算提交率百分比
const getSubmissionPercentage = computed(() => {
  const stats = studentData.value?.activities?.submissions_stats;
  if (!stats || !stats.total) return 0;
  return Math.round((stats.graded / stats.total) * 100);
});

// 格式化进度条显示
const format = (percentage) => {
  return `${percentage}%`;
};

// 格式化日期显示
const formatDate = (dateString) => {
  if (!dateString) return '未登录';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
};

// 格式化日期时间显示
const formatDateTime = (dateString) => {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

// 格式化分数显示
const formatScore = (score) => {
  if (score === null || score === undefined) return '无';
  return score.toFixed(1);
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

onMounted(fetchStudentDetail);
</script>

<style scoped>
.student-detail {
  padding: 20px;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-container {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.last-submission {
  background-color: #f5f7fa;
}

.last-submission h5 {
  margin-top: 0;
  color: #303133;
}

.other-item {
  text-align: center;
  padding: 10px;
}

.download-count {
  font-size: 24px;
  font-weight: bold;
  color: #67c23a;
}
</style>