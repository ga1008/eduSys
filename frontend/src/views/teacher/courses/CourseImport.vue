<!-- /src/views/teacher/courses/CourseImport.vue -->
<template>
  <div>
    <h2>导入课程</h2>

    <el-alert
      type="info"
      :closable="false"
      show-icon>
      <p>您可以从管理员分配的课程中进行导入。导入后，您将可以管理该课程的教学资料、进度和作业。</p>
    </el-alert>

    <div class="filter-container">
      <el-input
        v-model="searchQuery"
        placeholder="搜索课程名称"
        clearable
        style="width: 220px; margin-right: 10px;"
      />
      <el-button type="primary" @click="fetchAvailableCourses">搜索</el-button>
    </div>

    <el-table
      :data="availableCourses"
      v-loading="loading"
      border
      style="width: 100%; margin-top: 20px;">
      <el-table-column prop="course_name" label="课程名称" min-width="150" />
      <el-table-column prop="course_code" label="课程代码" min-width="120" />
      <el-table-column prop="class_name" label="班级" min-width="120" />
      <el-table-column prop="credit" label="学分" min-width="80" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="scope">
          <el-button
            type="primary"
            size="small"
            @click="importCourse(scope.row)"
            :loading="importLoading === scope.row.id">
            导入
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalItems"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 导入设置对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="课程导入设置"
      width="500px">
      <el-form :model="importForm" label-width="120px">
        <el-form-item label="课程名称">
          <span>{{ selectedCourse.course_name }}</span>
        </el-form-item>
        <el-form-item label="班级">
          <span>{{ selectedCourse.class_name }}</span>
        </el-form-item>
        <el-form-item label="教材" prop="textbook">
          <el-input v-model="importForm.textbook" placeholder="请输入使用的教材" />
        </el-form-item>
        <el-form-item label="开课日期" prop="start_date">
          <el-date-picker
            v-model="importForm.start_date"
            type="date"
            placeholder="选择开课日期"
            style="width: 100%" />
        </el-form-item>
        <el-form-item label="结课日期" prop="end_date">
          <el-date-picker
            v-model="importForm.end_date"
            type="date"
            placeholder="选择结课日期"
            style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmImport" :loading="confirmLoading">
            确认导入
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import couRequest from '@/utils/request_cou'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

// 数据和状态
const loading = ref(false)
const importLoading = ref(null)
const confirmLoading = ref(false)
const searchQuery = ref('')
const availableCourses = ref([])
const totalItems = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const importDialogVisible = ref(false)
const selectedCourse = ref({})

// 导入表单
const importForm = reactive({
  textbook: '',
  start_date: '',
  end_date: '',
  course: null,
  class_obj: null
})

// 获取可用课程
const fetchAvailableCourses = async () => {
  loading.value = true
  try {
    // 这里需要后端提供一个接口，获取教师可以导入的课程列表
    const response = await couRequest.get('/available-courses/', {
      params: {
        search: searchQuery.value,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    availableCourses.value = response.data.results
    totalItems.value = response.data.count
  } catch (error) {
    ElMessage.error('获取可用课程失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  fetchAvailableCourses()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchAvailableCourses()
}

// 导入课程
const importCourse = (course) => {
  selectedCourse.value = course
  importForm.course = course.course_id
  importForm.class_obj = course.class_id
  importDialogVisible.value = true
}

// 确认导入
const confirmImport = async () => {
  confirmLoading.value = true
  try {
    const response = await request.post('/teacher-course-classes/', {
      course: importForm.course,
      class_obj: importForm.class_obj,
      textbook: importForm.textbook,
      start_date: importForm.start_date,
      end_date: importForm.end_date,
      teacher: userStore.user.id // 当前教师ID
    })

    ElMessage.success('课程导入成功')
    importDialogVisible.value = false
    router.push('/teacher/courses')
  } catch (error) {
    ElMessage.error('课程导入失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    confirmLoading.value = false
  }
}

onMounted(() => {
  fetchAvailableCourses()
})
</script>

<style scoped>
.filter-container {
  margin: 20px 0;
  display: flex;
  align-items: center;
}
.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style>