<!-- 教师课程班级列表 -->
<template>
  <div>
    <h2>我的课程班级</h2>

    <div class="toolbar">
      <div class="left-tools">
        <el-button type="primary" @click="importCourse">
          <el-icon>
            <Plus/>
          </el-icon>
          导入课程
        </el-button>
        <el-button
            v-if="userStore.user.is_superuser"
            type="success"
            @click="createCourse">
          <el-icon>
            <Plus/>
          </el-icon>
          新建课程班级
        </el-button>
      </div>
      <el-input
          v-model="searchQuery"
          placeholder="搜索课程或班级"
          prefix-icon="el-icon-search"
          clearable
          style="width: 220px"
      />
    </div>

    <el-table
        :data="filteredCourseClasses"
        v-loading="loading"
        border
        style="width: 100%">
      <el-table-column prop="course_name" label="课程" min-width="150"/>
      <el-table-column prop="class_name" label="班级" min-width="120"/>
      <el-table-column label="教学时间" min-width="180">
        <template #default="scope">
          <div v-if="scope.row.start_date">
            {{ formatDate(scope.row.start_date) }} 至 {{ formatDate(scope.row.end_date) }}
          </div>
          <div v-else>
            <el-tag size="small" type="info">未设置</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="教学周" min-width="120">
        <template #default="scope">
          <div v-if="scope.row.start_week">
            第 {{ scope.row.start_week }} - {{ scope.row.end_week }} 周
          </div>
          <div v-else>
            <el-tag size="small" type="info">未设置</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="students_count" label="学生人数" min-width="90"/>
      <el-table-column label="操作" min-width="280" fixed="right">
        <template #default="scope">
          <el-button
              type="primary"
              size="small"
              @click="enterChatRoom(scope.row)">
            聊天室
          </el-button>
          <el-button
              type="success"
              size="small"
              @click="manageCourseProgress(scope.row)">
            进度
          </el-button>
          <el-button
              type="warning"
              size="small"
              @click="manageHomework(scope.row)">
            作业
          </el-button>
          <el-button
              type="info"
              size="small"
              @click="viewStudents(scope.row)">
            学生
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty
        v-if="!loading && courseClasses.length === 0"
        description="暂无课程数据">
      <el-button type="primary" @click="importCourse">导入课程</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/store/user'
import {fetchTeacherCourseClasses} from '@/api/teachers.js'
import {ElMessage} from 'element-plus'
import {Plus} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const courseClasses = ref([])
const loading = ref(false)
const searchQuery = ref('')

// 添加导入课程函数
const importCourse = () => {
  router.push('/teacher/courses/import')
}

// 添加创建课程班级函数（仅管理员可见）
const createCourse = () => {
  router.push('/teacher/courses/create')
}

// 加载课程班级数据
const loadCourseClasses = async () => {
  loading.value = true
  try {
    const response = await fetchTeacherCourseClasses()
    courseClasses.value = response.data
  } catch (error) {
    ElMessage.error('加载课程班级失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

// 搜索过滤
const filteredCourseClasses = computed(() => {
  if (!searchQuery.value) return courseClasses.value

  const query = searchQuery.value.toLowerCase()
  return courseClasses.value.filter(item =>
      item.course_name.toLowerCase().includes(query) ||
      item.class_name.toLowerCase().includes(query) ||
      (item.textbook && item.textbook.toLowerCase().includes(query))
  )
})

// 编辑课程班级
const editCourseClass = (item) => {
  router.push(`/teacher/courses/edit/${item.id}`)
}

// 管理课程进度
const manageCourseProgress = (item) => {
  router.push(`/teacher/courses/progress/${item.id}`)
}

// 管理作业
const manageHomework = (item) => {
  router.push(`/teacher/courses/homeworks/${item.id}`)
}

// 查看学生名单
const viewStudents = (item) => {
  router.push(`/teacher/courses/students/${item.id}`)
}

// 新增：进入聊天室
const enterChatRoom = (item) => {
  router.push({name: 'TeacherChatRoom', params: {id: item.id}})
}

onMounted(loadCourseClasses)
</script>

<style scoped>
.toolbar {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-tools {
  display: flex;
  gap: 10px;
}
</style>