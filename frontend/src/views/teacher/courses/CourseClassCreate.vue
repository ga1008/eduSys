<!-- /src/views/teacher/courses/CourseClassCreate.vue -->
<template>
  <div>
    <h2>新建课程班级</h2>

    <el-alert
      v-if="!userStore.user.is_superuser"
      type="warning"
      :closable="false"
      show-icon>
      <p>您无权创建课程班级关联，请联系管理员。</p>
    </el-alert>

    <el-form
      v-else
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      v-loading="loading"
      style="max-width: 700px; margin-top: 20px">

      <el-form-item label="课程" prop="course">
        <el-select
          v-model="form.course"
          filterable
          remote
          :remote-method="searchCourses"
          placeholder="请选择课程"
          style="width: 100%">
          <el-option
            v-for="item in courseOptions"
            :key="item.id"
            :label="item.name + ' (' + item.code + ')'"
            :value="item.id">
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="班级" prop="class_obj">
        <el-select
          v-model="form.class_obj"
          filterable
          remote
          :remote-method="searchClasses"
          placeholder="请选择班级"
          style="width: 100%">
          <el-option
            v-for="item in classOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id">
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="教师" prop="teacher">
        <el-select
          v-model="form.teacher"
          filterable
          remote
          :remote-method="searchTeachers"
          placeholder="请选择教师"
          style="width: 100%">
          <el-option
            v-for="item in teacherOptions"
            :key="item.id"
            :label="item.name || item.username"
            :value="item.id">
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="教材" prop="textbook">
        <el-input v-model="form.textbook" placeholder="请输入使用的教材" />
      </el-form-item>

      <el-form-item label="开课日期" prop="start_date">
        <el-date-picker
          v-model="form.start_date"
          type="date"
          placeholder="选择开课日期"
          style="width: 100%" />
      </el-form-item>

      <el-form-item label="结课日期" prop="end_date">
        <el-date-picker
          v-model="form.end_date"
          type="date"
          placeholder="选择结课日期"
          style="width: 100%" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">创建</el-button>
        <el-button @click="$router.push('/teacher/courses')">返回</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

// 选项数据
const courseOptions = ref([])
const classOptions = ref([])
const teacherOptions = ref([])

// 表单数据
const form = reactive({
  course: null,
  class_obj: null,
  teacher: null,
  textbook: '',
  syllabus: '',
  start_date: '',
  end_date: '',
  start_week: null,
  end_week: null
})

// 表单验证规则
const rules = {
  course: [{ required: true, message: '请选择课程', trigger: 'change' }],
  class_obj: [{ required: true, message: '请选择班级', trigger: 'change' }],
  teacher: [{ required: true, message: '请选择教师', trigger: 'change' }],
  start_date: [{ type: 'date', message: '请选择开课日期', trigger: 'change' }],
  end_date: [
    { type: 'date', message: '请选择结课日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (form.start_date && value && value < form.start_date) {
          callback(new Error('结课日期不能早于开课日期'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 搜索课程
const searchCourses = async (query) => {
  if (query) {
    try {
      const response = await request.get('/edu/api/courses/', {
        params: { search: query }
      })
      courseOptions.value = response.data.results || response.data
    } catch (error) {
      console.error('获取课程失败', error)
    }
  }
}

// 搜索班级
const searchClasses = async (query) => {
  if (query) {
    try {
      const response = await request.get('/edu/api/classes/', {
        params: { search: query }
      })
      classOptions.value = response.data.results || response.data
    } catch (error) {
      console.error('获取班级失败', error)
    }
  }
}

// 搜索教师
const searchTeachers = async (query) => {
  if (query) {
    try {
      const response = await request.get('/edu/api/teachers/', {
        params: { search: query }
      })
      teacherOptions.value = response.data.results || response.data
    } catch (error) {
      console.error('获取教师失败', error)
    }
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await request.post('/edu/api/teacher-course-classes/', form)
      ElMessage.success('创建成功')
      router.push('/teacher/courses')
    } catch (error) {
      ElMessage.error('创建失败：' + (error.response?.data?.detail || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}
</script>