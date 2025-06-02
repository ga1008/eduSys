<!-- 课程进度管理 -->
<template>
  <div>
    <div class="header-container">
      <h2>课程进度管理</h2>
      <div v-if="courseClass">
        <el-tag type="success">{{ courseClass.course_name }}</el-tag>
        <el-tag type="info" style="margin-left: 10px">{{ courseClass.class_name }}</el-tag>
      </div>
    </div>

    <el-card class="progress-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>当前教学进度</span>
          <el-button type="primary" size="small" @click="editProgress = true">
            更新进度
          </el-button>
        </div>
      </template>

      <div v-if="!editProgress">
        <div v-if="courseClass && courseClass.progress" class="progress-content">
          <div v-html="formattedProgress"></div>
        </div>
        <el-empty v-else description="暂无进度信息"></el-empty>
      </div>

      <div v-else>
        <el-form :model="progressForm" ref="progressFormRef">
          <el-form-item prop="progress">
            <el-input
              v-model="progressForm.progress"
              type="textarea"
              :rows="10"
              placeholder="请输入教学进度信息，可以使用简单的HTML格式"
            ></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveProgress">保存</el-button>
            <el-button @click="cancelEdit">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <el-card class="schedule-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>教学计划</span>
        </div>
      </template>

      <el-descriptions title="课程安排" direction="vertical" :column="1" border>
        <el-descriptions-item label="教材">{{ courseClass?.textbook || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="开课日期">{{ formatDate(courseClass?.start_date) }}</el-descriptions-item>
        <el-descriptions-item label="结课日期">{{ formatDate(courseClass?.end_date) }}</el-descriptions-item>
        <el-descriptions-item label="教学周">{{ courseClass?.start_week || '?' }} - {{ courseClass?.end_week || '?' }} 周</el-descriptions-item>
        <el-descriptions-item label="教学大纲">
          <div v-if="courseClass?.syllabus" v-html="courseClass.syllabus"></div>
          <span v-else>未设置</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchTeacherCourseClass } from '@/api/teachers'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const route = useRoute()
const courseClassId = computed(() => route.params.id)
const courseClass = ref(null)
const loading = ref(false)
const editProgress = ref(false)
const progressFormRef = ref(null)

// 进度表单
const progressForm = ref({
  progress: ''
})

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未设置'
  const date = new Date(dateString)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`
}

// 格式化进度显示（添加样式和换行）
const formattedProgress = computed(() => {
  if (!courseClass.value || !courseClass.value.progress) return ''

  // 保留换行并添加简单样式
  return courseClass.value.progress
    .replace(/\n/g, '<br>')
    .replace(/第(\d+)周/g, '<b style="color:#409EFF">第$1周</b>')
})

// 加载课程班级信息
const loadCourseClass = async () => {
  loading.value = true
  try {
    const response = await fetchTeacherCourseClass(courseClassId.value)
    courseClass.value = response.data
    // 初始化表单
    progressForm.value.progress = courseClass.value.progress || ''
  } catch (error) {
    ElMessage.error('加载课程班级信息失败')
  } finally {
    loading.value = false
  }
}

// 保存进度
const saveProgress = async () => {
  loading.value = true
  try {
    await request.patch(`/edu/api/teacher-course-classes/${courseClassId.value}/update_progress/`, {
      progress: progressForm.value.progress
    })

    // 更新本地数据
    courseClass.value.progress = progressForm.value.progress

    ElMessage.success('保存成功')
    editProgress.value = false
  } catch (error) {
    ElMessage.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  progressForm.value.progress = courseClass.value.progress || ''
  editProgress.value = false
}

onMounted(loadCourseClass)
</script>

<style scoped>
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

.progress-content {
  min-height: 100px;
  line-height: 1.6;
}
</style>