<!--课程创建组件-->
<template>
  <el-card>
    <h3>{{ isEdit ? '编辑课程' : '新建课程' }}</h3>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" class="mt-4">
      <el-form-item label="课程名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入课程名称"/>
      </el-form-item>

      <el-form-item label="课程代码" prop="code">
        <el-input v-model="form.code" placeholder="请输入课程代码"/>
      </el-form-item>

      <el-form-item label="学分" prop="credit">
        <el-input-number v-model="form.credit" :min="0" :max="10" :precision="1"/>
      </el-form-item>

      <el-form-item label="课时" prop="hours">
        <el-input-number v-model="form.hours" :min="0" :max="200"/>
      </el-form-item>

      <el-form-item label="课程描述" prop="description">
        <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入课程描述"/>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="save">{{ isEdit ? '保存' : '创建' }}</el-button>
        <el-button @click="router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchCourse, createCourse, updateCourse } from '@/api/courses'

const route = useRoute()
const router = useRouter()
const isEdit = !!route.params.id
const formRef = ref(null)
const form = ref({
  name: '',
  code: '',
  credit: 1,
  hours: 16,
  description: ''
})

// 表单校验规则
const rules = {
  name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入课程代码', trigger: 'blur' }
  ],
  credit: [
    { required: true, message: '请输入学分', trigger: 'blur' }
  ],
  hours: [
    { required: true, message: '请输入课时', trigger: 'blur' }
  ]
}

// 读取详情
onMounted(async () => {
  if (isEdit) {
    try {
      const { data } = await fetchCourse(route.params.id)
      form.value = {
        name: data.name,
        code: data.code,
        credit: data.credit,
        hours: data.hours,
        description: data.description || ''
      }
    } catch (e) {
      ElMessage.error('获取课程详情失败')
      console.error(e)
    }
  }
})

// 保存
const save = async () => {
  await formRef.value.validate()

  try {
    if (isEdit) {
      await updateCourse(route.params.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCourse(form.value)
      ElMessage.success('创建成功')
    }
    router.push('/admin/courses')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || '未知错误'))
    console.error(e)
  }
}
</script>

<style scoped>
.mt-4{margin-top:20px}
</style>