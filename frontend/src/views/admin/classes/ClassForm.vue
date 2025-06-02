<script setup>
import { ref, onMounted } from 'vue'
import { useRoute,useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchClass, createClass, updateClass } from '@/api/classes'

const route     = useRoute()
const router    = useRouter()
const isEdit    = !!route.params.id
const formRef   = ref(null)
const form      = ref({ name:'', grade:'', department:'', major:'', remarks:'' })

// 读取详情
onMounted(async () => {
  if (isEdit) {
    const { data } = await fetchClass(route.params.id)
    form.value = {
      name: data.name,
      grade: data.year ? String(data.year) : '', // 使用year字段代替grade
      department: data.department || '',
      major: data.major || '',
      remarks: data.description || '' // 使用description字段代替remarks
    }
  }
})

// 保存
const save = async () => {
  await formRef.value.validate()
  // 创建与API匹配的数据格式
  const apiData = {
    name: form.value.name,
    year: parseInt(form.value.grade), // 将grade转换为year
    department: form.value.department || '', // 确保department存在
    major: form.value.major || '', // 确保major存在
    description: form.value.remarks // 将remarks转换为description
  }

  if (isEdit) {
    await updateClass(route.params.id, apiData)
    ElMessage.success('更新成功')
  } else {
    await createClass(apiData)
    ElMessage.success('创建成功')
  }
  router.push('/admin/classes')
}

// 表单校验
const rules = {
  name :[{required:true,message:'请输入班级名称',trigger:'blur'}],
  department:[{required:true,message:'请输入所属院系',trigger:'blur'}],
  major:[{required:true,message:'请输入所属专业',trigger:'blur'}],
  grade:[{required:true,message:'请选择年级',trigger:'change'}]
}
</script>

<template>
  <el-card>
    <h3>{{ isEdit ? '编辑班级' : '新建班级' }}</h3>

    <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" class="mt-4">
      <el-form-item label="班级名称" prop="name">
        <el-input v-model="form.name"/>
      </el-form-item>

      <el-form-item label="年级" prop="grade">
        <el-select v-model="form.grade" placeholder="请选择">
          <el-option v-for="y in [2020,2021,2022,2023,2024]" :key="y" :label="`${y}级`" :value="String(y)"/>
        </el-select>
      </el-form-item>
      <el-form-item label="院系" prop="department">
        <el-input v-model="form.department" placeholder="请输入所属院系"/>
      </el-form-item>
      <el-form-item label="专业" prop="major">
        <el-input v-model="form.major" placeholder="请输入所属专业"/>
      </el-form-item>

      <el-form-item label="备注">
        <el-input v-model="form.remarks" type="textarea" rows="3"/>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="save">{{ isEdit ? '保存' : '创建' }}</el-button>
        <el-button @click="router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.mt-4{margin-top:20px}
</style>
