<!--教师信息更改表单-->
<!-- 教师信息表单 -->
<template>
  <div>
    <h2>{{ isEdit ? '编辑教师' : '添加教师' }}</h2>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      style="max-width: 600px"
      v-loading="loading">

      <el-form-item label="工号" prop="teacher_number">
        <el-input v-model="form.teacher_number" :disabled="isEdit" />
      </el-form-item>

      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" type="email" />
      </el-form-item>

      <el-form-item label="密码" prop="password" v-if="!isEdit">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>

      <el-form-item label="性别" prop="gender">
        <el-select v-model="form.gender" placeholder="请选择性别">
          <el-option label="男" value="M" />
          <el-option label="女" value="F" />
          <el-option label="其他" value="O" />
        </el-select>
      </el-form-item>

      <el-form-item label="电话" prop="phone">
        <el-input v-model="form.phone" />
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
import { fetchTeacher, createTeacher, updateTeacher } from '@/api/teachers'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)

// 判断是编辑还是新增
const isEdit = computed(() => Boolean(route.params.id))

// 表单数据
const form = reactive({
  teacher_number: '',
  name: '',
  email: '',
  password: '',
  gender: 'M',
  phone: ''
})

// 表单验证规则
const rules = {
  teacher_number: [
    { required: true, message: '请输入教师工号', trigger: 'blur' },
    { pattern: /^\S+$/, message: '工号不能包含空格', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入教师姓名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: !isEdit.value, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

// 加载教师数据（编辑模式）
const loadTeacher = async () => {
  if (!isEdit.value) return

  loading.value = true
  try {
    const { data } = await fetchTeacher(route.params.id)
    Object.keys(form).forEach(key => {
      if (key !== 'password' && data[key] !== undefined) {
        form[key] = data[key]
      }
    })
  } catch (error) {
    ElMessage.error('获取教师信息失败')
    console.error(error)
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
      // 移除密码（如果编辑模式且密码为空）
      const formData = { ...form }
      if (isEdit.value && !formData.password) {
        delete formData.password
      }

      if (isEdit.value) {
        await updateTeacher(route.params.id, formData)
        ElMessage.success('更新成功')
      } else {
        await createTeacher(formData)
        ElMessage.success('添加成功')
      }
      goBack()
    } catch (error) {
      ElMessage.error(isEdit.value ? '更新失败' : '添加失败')
      console.error(error)
    } finally {
      loading.value = false
    }
  })
}

// 返回列表页面
const goBack = () => {
  router.push('/admin/teachers')
}

onMounted(loadTeacher)
</script>