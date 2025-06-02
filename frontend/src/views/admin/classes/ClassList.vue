<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchClasses, deleteClass, fetchStudentsCount
} from '@/api/classes'
import { ElMessage, ElMessageBox } from 'element-plus'

const router        = useRouter()
const rows          = ref([])
const loading       = ref(false)
const searchQuery   = ref('')

// 拉取班级
const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchClasses()
    rows.value = data.map(item => ({
      ...item,
      // 如果后端没有直接返回 student_count，这里临时设置一个默认值
      student_count: item.student_count || 0
    }))
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r =>
    r.name.toLowerCase().includes(q) ||
    (r.year && String(r.year).includes(q))
  )
})

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除班级「${row.name}」吗？`, '警告', { type:'warning' })
    await deleteClass(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* 取消或失败 */ }
}

onMounted(loadData)
</script>

<template>
  <div>
    <h2>班级管理</h2>

    <div class="toolbar">
      <el-button type="primary" @click="router.push('/admin/classes/new')">新建班级</el-button>
      <el-input v-model="searchQuery" placeholder="搜索班级..." clearable style="width:260px" />
    </div>

    <el-table :data="filteredRows" border v-loading="loading" style="width:100%">
    <el-table-column prop="id" label="ID" width="80"/>
    <el-table-column prop="name" label="班级名称"/>
    <el-table-column label="年级" width="120">
      <template #default="{row}">{{ row.year }}级</template>
    </el-table-column>
    <el-table-column label="学院" width="120">
      <template #default="{row}">{{ row.department }}</template>
    </el-table-column>
    <el-table-column label="专业" width="120">
      <template #default="{row}">{{ row.major }}</template>
    </el-table-column>
    <el-table-column label="学生数" width="120">
      <template #default="{row}">{{ row.student_count || '0' }}</template>
    </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="scope">
          <el-button size="small" type="primary"  @click="router.push(`/admin/classes/${scope.row.id}/edit`)">编辑</el-button>
          <el-button size="small" type="success"  @click="router.push(`/admin/classes/${scope.row.id}/students`)">学生</el-button>
          <el-button size="small" type="danger"   @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.toolbar{display:flex;gap:10px;margin:16px 0}
</style>
