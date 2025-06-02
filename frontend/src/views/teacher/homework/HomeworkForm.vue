<!-- 作业表单 -->
<template>
  <div>
    <h2>{{ isEdit ? '编辑作业' : '创建作业' }}</h2>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      v-loading="loading"
      style="max-width: 700px">

      <el-descriptions
        v-if="courseClass"
        title="课程信息"
        :column="1"
        border
        style="margin-bottom: 20px">
        <el-descriptions-item label="课程名称">{{ courseClass.course_name }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ courseClass.class_name }}</el-descriptions-item>
      </el-descriptions>

      <el-form-item label="作业标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入作业标题" />
      </el-form-item>

      <el-form-item label="作业描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          rows="5"
          placeholder="请输入作业描述和要求" />
      </el-form-item>

      <el-form-item label="截止日期" prop="due_date">
        <el-date-picker
          v-model="form.due_date"
          type="datetime"
          placeholder="选择截止日期"
          style="width: 100%" />
      </el-form-item>

      <el-form-item label="满分值" prop="max_score">
        <el-input-number
          v-model="form.max_score"
          :min="0"
          :max="1000"
          :step="5"
          :precision="2" />
      </el-form-item>

      <el-form-item label="状态" prop="active">
        <el-switch
          v-model="form.active"
          active-text="启用"
          inactive-text="禁用" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">保存</el-button>
        <el-button @click="goBack">返回</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { fetchTeacherCourseClass } from '@/api/teachers'
import { fetchHomework, createHomework, updateHomework } from '@/api/homeworks'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const courseClass = ref(null)

// 判断是编辑还是创建
const isEdit = computed(() => Boolean(route.params.homeworkId))
const courseClassId = computed(() => route.params.id)

// 表单数据
const form = reactive({
  title: '',
  description: '',
  due_date: '',
  max_score: 100,
  active: true,
  course_class: ''
})

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入作业标题', trigger: 'blur' },
    { min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
  ],
  due_date: [
    { required: true, message: '请选择截止日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value && new Date(value) < new Date()) {
          callback(new Error('截止日期不能早于当前时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  max_score: [
    { required: true, message: '请设置满分值', trigger: 'blur' }
  ]
}

// 加载课程班级信息
const loadCourseClass = async () => {
  try {
    const response = await fetchTeacherCourseClass(courseClassId.value)
    courseClass.value = response.data
    form.course_class = courseClassId.value
  } catch (error) {
    ElMessage.error('加载课程班级信息失败')
  }
}

// 加载作业数据（编辑模式）
const loadHomework = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    const response = await fetchHomework(route.params.homeworkId)
    const data = response.data

    form.title = data.title
    form.description = data.description || ''
    form.due_date = data.due_date ? new Date(data.due_date) : ''
    form.max_score = data.max_score
    form.active = data.active
    form.course_class = data.course_class
  } catch (error) {
    ElMessage.error('加载作业数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (isEdit.value) {
        await updateHomework(route.params.homeworkId, form)
        ElMessage.success('更新成功')
      } else {
        await createHomework(form)
        ElMessage.success('创建成功')
      }
      goBack()
    } catch (error) {
      ElMessage.error('保存失败：' + (error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}

// 返回作业列表
const goBack = () => {
  router.push(`/teacher/courses/homeworks/${courseClassId.value}`)
}

onMounted(() => {
  loadCourseClass()
  loadHomework()
})
</script>