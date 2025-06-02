<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  fetchStudents, importStudents, clearStudents, fetchClass,
  downloadTpl, createStudent, updateStudent, deleteStudent
} from '@/api/classes'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const props = defineProps({ classId: [String, Number] })
const route = useRoute()
const classId = props.classId ?? route.params.id

const students = ref([])
const loading = ref(false)
const searchKey = ref('')
const className = ref('')

const fileInput = ref(null)
const importDialog = ref(false)
const importing = ref(false)
const importProgress = ref(0)
const importResult = ref(null)

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = ref({
  student_number: '', name: '', email: '', gender: 'M',
  phone: '', qq: '', password: '123456', class_enrolled: classId
})
const rules = {
  student_number: [{ required: true, message: '必填', trigger: 'blur' }],
  name: [{ required: true, message: '必填', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式错误', trigger: 'blur' }]
}

const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchStudents(classId)
    students.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch (e) {
    console.error(e)
    ElMessage.error('获取学生列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await fetchClass(classId)
    className.value = data.name
  } catch (e) {
    console.error('获取班级信息失败', e)
  }

  await loadData()
})

const rows = computed(() => {
  if (!searchKey.value) return students.value
  const q = searchKey.value.toLowerCase()
  return students.value.filter(s =>
    (s.name && s.name.toLowerCase().includes(q)) ||
    (s.student_number && s.student_number.toLowerCase().includes(q)) ||
    (s.email && s.email.toLowerCase().includes(q))
  )
})

const triggerUpload = () => fileInput.value.click()

const handleFile = async (e) => {
  const file = e.target.files[0]
  if (!file) return

  const fd = new FormData()
  fd.append('file', file)

  importDialog.value = true
  importing.value = true
  importProgress.value = 20

  const timer = setInterval(() => {
    if (importProgress.value < 85) importProgress.value += 5
  }, 400)

  try {
    const { data } = await importStudents(classId, fd)
    clearInterval(timer)
    importProgress.value = 100
    importResult.value = data
    ElMessage.success(`成功导入 ${data.stats.success} 条`)
    await loadData()
  } catch (err) {
    clearInterval(timer)
    console.error(err)
    importResult.value = null
    ElMessage.error('导入失败，请检查文件格式或稍后重试')
  } finally {
    importing.value = false
  }
}

const downloadTemplate = async () => {
  try {
    const { data } = await downloadTpl()
    const url = URL.createObjectURL(new Blob([data]))
    const a = document.createElement('a')
    a.href = url
    a.download = '学生导入模板.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
    ElMessage.error('下载模板失败')
  }
}

const clearAll = async () => {
  try {
    await ElMessageBox.confirm('确定清空该班级的所有学生吗？此操作不可恢复！',
      '危险操作', { type: 'warning' })
    await clearStudents(classId)
    ElMessage.success('已清空')
    await loadData()
  } catch { }
}

const openForm = (row = null) => {
  isEdit.value = !!row
  form.value = row
    ? { ...row, password: '' }
    : { student_number: '', name: '', email: '', gender: 'M',
        phone: '', qq: '', password: '123456', class_enrolled: classId }
  dialogVisible.value = true
}

const saveStudent = async () => {
  try {
    await formRef.value.validate()
    if (isEdit.value) {
      await updateStudent(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createStudent(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e) {
    if (e !== false) {
      console.error(e)
      ElMessage.error('保存失败')
    }
  }
}

const removeStudent = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除学生「${row.name}」吗？`, '警告', { type: 'warning' })
    await deleteStudent(row.id)
    ElMessage.success('已删除')
    await loadData()
  } catch { }
}
</script>

<template>
  <div>
    <el-card class="mb-4">
      <template #header>
        <span>班级：{{ className || `ID:${classId}` }} — 学生管理</span>
        <div class="button-group">
          <el-button size="small" @click="downloadTemplate">下载模板</el-button>
          <el-button size="small" type="success" @click="triggerUpload">
            <el-icon><Upload /></el-icon> 导入
          </el-button>
          <input type="file" ref="fileInput" @change="handleFile"
                 accept=".xlsx,.csv" hidden />
          <el-button size="small" type="danger" @click="clearAll">清空</el-button>
          <el-button size="small" type="primary" @click="openForm()">新增学生</el-button>
        </div>
      </template>

      <el-input v-model="searchKey" placeholder="搜索姓名/学号/邮箱" clearable class="mb-3"/>

      <el-table :data="rows" border v-loading="loading">
        <el-table-column type="index" width="60"/>
        <el-table-column prop="student_number" label="学号" width="120"/>
        <el-table-column prop="name" label="姓名"/>
        <el-table-column prop="email" label="邮箱"/>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="openForm(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeStudent(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑学生' : '新增学生'">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="学号" prop="student_number">
          <el-input v-model="form.student_number" :disabled="isEdit"/>
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name"/>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email"/>
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender">
            <el-option label="男" value="M"/><el-option label="女" value="F"/><el-option label="其他" value="O"/>
          </el-select>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone"/>
        </el-form-item>
        <el-form-item label="QQ">
          <el-input v-model="form.qq"/>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码">
          <el-input v-model="form.password" type="password" placeholder="留空默认 123456"/>
        </el-form-item>
        <el-form-item v-if="isEdit" label="重置密码">
          <el-input v-model="form.password" type="password" placeholder="留空不修改"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStudent">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="importDialog" title="批量导入学生" width="450px"
               :close-on-click-modal="false" :show-close="!importing">
      <div v-if="importing">
        <el-progress :percentage="importProgress"/>
        <p style="text-align:center;margin-top:10px">正在导入，请稍候...</p>
      </div>
      <div v-else-if="importResult">
        <el-alert
          :title="`成功 ${importResult.stats.success} 条，失败 ${importResult.stats.failed} 条`"
          :type="importResult.stats.failed ? 'warning' : 'success'"
          show-icon :closable="false"
        />
        <ul v-if="importResult.stats.failed" style="margin-top:10px;padding-left:18px">
          <li v-for="(err,i) in importResult.stats.errors" :key="i" style="color:#f56c6c">
            {{ err }}
          </li>
        </ul>
      </div>
      <template #footer>
        <el-button :disabled="importing" @click="importDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.button-group {
  float: right;
}
</style>