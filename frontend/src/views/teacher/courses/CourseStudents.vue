<!-- 课程学生列表 -->
<template>
  <div>
    <div class="header-container">
      <h2>课程学生名单</h2>

      <!-- 课程选择器 -->
      <el-select
        v-model="selectedCourseId"
        placeholder="请选择课程班级"
        @change="handleCourseChange"
        style="width: 300px"
        filterable
        v-loading="coursesLoading"
      >
        <el-option
          v-for="item in teacherCourses"
          :key="item.id"
          :label="`${item.course_name} - ${item.class_name}`"
          :value="item.id"
        />
      </el-select>
    </div>

    <div v-if="courseClass" class="course-info">
      <el-tag type="success">{{ courseClass.course_name }}</el-tag>
      <el-tag type="info" style="margin-left: 10px">{{ courseClass.class_name }}</el-tag>
    </div>

    <div class="toolbar" v-if="selectedCourseId">
      <div>
        <span class="student-count">总学生数: {{ students.length }}</span>
      </div>
      <el-input
        v-model="searchQuery"
        placeholder="搜索学生姓名、学号等"
        prefix-icon="el-icon-search"
        clearable
        style="width: 220px"
      />
    </div>

    <el-empty v-if="!selectedCourseId" description="请选择一个课程班级" />

    <el-table
      v-if="selectedCourseId"
      :data="filteredStudents"
      v-loading="loading"
      border
      style="width: 100%">
      <el-table-column prop="student_number" label="学号" min-width="120" />
      <el-table-column prop="name" label="姓名" min-width="100" />
      <el-table-column label="性别" min-width="80">
        <template #default="scope">
          {{ formatGender(scope.row.gender) }}
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="电话" min-width="140" />
      <el-table-column prop="qq" label="QQ" min-width="120" />
      <el-table-column label="操作" min-width="120" fixed="right">
        <template #default="scope">
          <el-button
            type="primary"
            size="small"
            @click="viewStudentDetail(scope.row)">
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {fetchTeacherCourseClass, fetchTeacherCourseClassStudents, fetchTeacherCourseClasses} from '@/api/teachers.js'
import {ElMessage} from 'element-plus'
import couRequest from '@/utils/request_cou'

const router = useRouter()
const route = useRoute()
const courseClassId = computed(() => route.params.id)
const selectedCourseId = ref('')
const courseClass = ref(null)
const students = ref([])
const loading = ref(false)
const searchQuery = ref('')
const teacherCourses = ref([])
const coursesLoading = ref(false)

// 监听路由参数变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    selectedCourseId.value = newId
  }
})

// 监听选中课程变化
watch(selectedCourseId, (newId) => {
  if (newId) {
    loadCourseClass(newId)
    loadStudents(newId)
    // 更新URL，但不重新加载组件
    if (newId !== route.params.id) {
      router.push(`/teacher/courses/students/${newId}`)
    }
  } else {
    courseClass.value = null
    students.value = []
  }
})

// 加载教师所有课程班级
const loadTeacherCourses = async () => {
  coursesLoading.value = true
  try {
    const response = await fetchTeacherCourseClasses()
    teacherCourses.value = response.data

    // 如果URL中有ID参数，则设置选中的课程
    if (courseClassId.value) {
      selectedCourseId.value = courseClassId.value
    }
    // 如果没有URL参数但有课程，则默认选中第一个
    else if (teacherCourses.value.length > 0) {
      selectedCourseId.value = teacherCourses.value[0].id
    }
  } catch (error) {
    console.error('加载教师课程失败:', error)
    ElMessage.error('加载教师课程失败：' + (error.message || '未知错误'))
  } finally {
    coursesLoading.value = false
  }
}

// 课程切换处理
const handleCourseChange = (courseId) => {
  if (courseId) {
    selectedCourseId.value = courseId
  }
}

// 加载课程班级信息
const loadCourseClass = async (id) => {
  try {
    const response = await fetchTeacherCourseClass(id)
    courseClass.value = response.data
  } catch (error) {
    console.error('加载课程班级信息失败:', error)
    ElMessage.error('加载课程班级信息失败：' + (error.message || '未知错误'))
  }
}

// 加载学生列表
const loadStudents = async (id) => {
  loading.value = true
  try {
    const response = await fetchTeacherCourseClassStudents(id)
    students.value = response.data
  } catch (error) {
    console.error('加载学生列表失败:', error)
    ElMessage.error('加载学生列表失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 格式化性别
const formatGender = (gender) => {
  if (gender === 'M') return '男'
  if (gender === 'F') return '女'
  return '其他'
}

// 搜索过滤
const filteredStudents = computed(() => {
  if (!searchQuery.value) return students.value

  const query = searchQuery.value.toLowerCase()
  return students.value.filter(item =>
    item.name?.toLowerCase().includes(query) ||
    item.student_number?.toLowerCase().includes(query) ||
    item.email?.toLowerCase().includes(query) ||
    item.phone?.toLowerCase().includes(query) ||
    item.qq?.toLowerCase().includes(query)
  )
})

// 查看学生详情
const viewStudentDetail = (student) => {
  // 使用路由跳转而不是直接请求API
  router.push(`/teacher/courses/${courseClassId.value}/students/${student.id}`)
}

onMounted(() => {
  loadTeacherCourses()
})
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.course-info {
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin: 20px 0;
}

.student-count {
  font-size: 16px;
  font-weight: bold;
}
</style>