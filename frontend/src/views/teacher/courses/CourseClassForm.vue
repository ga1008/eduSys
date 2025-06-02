<!-- 课程班级设置表单 -->
<template>
  <div class="course-form">
    <h2>{{ isNew ? '添加课程班级' : '课程班级设置' }}</h2>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      v-loading="loading"
      style="max-width: 720px">

      <el-descriptions title="基本信息" :column="1" border>
        <el-descriptions-item label="课程名称">{{ courseData.course_name }}</el-descriptions-item>
        <el-descriptions-item label="班级">{{ courseData.class_name }}</el-descriptions-item>
        <el-descriptions-item label="教师">{{ courseData.teacher_name }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">教学安排</el-divider>

      <el-form-item label="课程" prop="course" style="display: none">
        <el-input v-model="form.course" placeholder="课程" />
      </el-form-item>

      <el-form-item label="班级" prop="class_obj"  style="display: none">
        <el-input v-model="form.class_obj" placeholder="班级" />
      </el-form-item>

      <el-form-item label="教师" prop="teacher" style="display: none">
        <el-input v-model="form.teacher" placeholder="教师" />
      </el-form-item>

      <el-form-item label="教材" prop="textbook">
        <el-input v-model="form.textbook" placeholder="请输入使用的教材" />
      </el-form-item>

      <el-form-item label="教学大纲" prop="syllabus">
        <el-input
          v-model="form.syllabus"
          type="textarea"
          :rows="4"
          placeholder="请输入教学大纲" />
      </el-form-item>

      <el-form-item label="开课时间" prop="start_date">
        <el-date-picker
          v-model="form.start_date"
          type="date"
          placeholder="选择开始日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="结课时间" prop="end_date">
        <el-date-picker
          v-model="form.end_date"
          type="date"
          placeholder="选择结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>


      <el-form-item label="开始周" prop="start_week">
        <el-input-number
          v-model="form.start_week"
          :min="1"
          :max="20"
          placeholder="开始教学周" />
      </el-form-item>

      <el-form-item label="结束周" prop="end_week">
        <el-input-number
          v-model="form.end_week"
          :min="form.start_week || 1"
          :max="30"
          placeholder="结束教学周" />
      </el-form-item>

      <div class="form-footer">
        <el-form-item>
          <el-button type="primary" @click="submitForm">保存</el-button>
          <el-button @click="goBack">返回</el-button>
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { updateTeacherCourseClass } from '@/api/courses'
import { fetchTeacherCourseClass } from '@/api/teachers'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const courseData = ref({})

// 判断是否是新建
const isNew = computed(() => !route.params.id)

// 表单数据
const form = reactive({
  textbook: '',
  syllabus: '',
  progress: '',
  start_date: '',
  end_date: '',
  start_week: null,
  end_week: null,
  course: null,
  class_obj: null,
  teacher: null
})

// 表单验证规则
const rules = {
  start_date: [
    { type: 'date', message: '请选择开课日期', trigger: 'change' }
  ],
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
  ],
  start_week: [
    { type: 'number', message: '请输入开始周', trigger: 'blur' }
  ],
  end_week: [
    { type: 'number', message: '请输入结束周', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (form.start_week && value && value < form.start_week) {
          callback(new Error('结束周不能早于开始周'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 加载课程班级数据
const loadCourseClass = async () => {
  if (isNew.value) return

  const id = route.params.id
  loading.value = true

  try {
    const response = await fetchTeacherCourseClass(id)
    const data = response.data

    // 保存完整数据用于显示
    courseData.value = data

    // 填充表单数据
    form.textbook = data.textbook || ''
    form.syllabus = data.syllabus || ''
    form.progress = data.progress || ''
    form.start_date = data.start_date ? new Date(data.start_date) : null
    form.end_date = data.end_date ? new Date(data.end_date) : null
    form.start_week = data.start_week
    form.end_week = data.end_week
    form.course = data.course.id
    form.class_obj = data.class_obj.id
    form.teacher = data.teacher.id
  } catch (error) {
    ElMessage.error('加载课程班级数据失败：' + (error.message || '未知错误'))
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
      const id = route.params.id
      await updateTeacherCourseClass(id, form)
      ElMessage.success('保存成功')
      goBack()
    } catch (error) {
      ElMessage.error('保存失败：' + (error.message || '未知错误'))
    } finally {
      loading.value = false
    }
  })
}

// 返回列表
const goBack = () => {
  router.push('/teacher/courses')
}

onMounted(loadCourseClass)
</script>

<style scoped>
.course-form {
  /* 让表单内容居中，限制最大宽度 */
  max-width: 600px;
  margin: 40px auto;
  padding: 24px;
  background-color: #f9f9f9;  /* 浅灰背景 */
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* 调整 label 宽度和行距 */
.course-form .el-form-item__label {
  width: 100px;
  font-weight: 500;
}

/* 调整表单项之间的间距 */
.course-form .el-form-item {
  margin-bottom: 20px;
}

/* 提交按钮区域在底部对齐 */
.form-footer {
  text-align: right;
  margin-top: 30px;
}
</style>
