<!--课程列组件-->
<template>
  <div>
    <h2>课程管理</h2>

    <div class="toolbar">
      <el-button type="primary" @click="router.push('/admin/courses/new')">新建课程</el-button>
      <el-input v-model="searchQuery" placeholder="搜索课程..." clearable style="width:260px" />
    </div>

    <el-table :data="filteredRows" border v-loading="loading" style="width:100%">
      <el-table-column prop="id" label="ID" width="80"/>
      <el-table-column prop="name" label="课程名称"/>
      <el-table-column prop="code" label="课程代码"/>
      <el-table-column prop="credit" label="学分" width="100"/>
      <el-table-column prop="hours" label="课时" width="100"/>
      <el-table-column prop="description" label="课程描述" show-overflow-tooltip/>
      <el-table-column label="操作" width="240">
        <template #default="scope">
          <el-button size="small" type="primary" @click="router.push(`/admin/courses/${scope.row.id}/edit`)">编辑</el-button>
          <el-button size="small" type="success" @click="router.push(`/admin/courses/${scope.row.id}/classes`)">班级</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  fetchCourses, deleteCourse
} from '@/api/courses'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const rows = ref([])
const loading = ref(false)
const searchQuery = ref('')

// 拉取课程列表
const loadData = async () => {
  loading.value = true
  try {
    const { data } = await fetchCourses()
    rows.value = data
  } finally {
    loading.value = false
  }
}

const filteredRows = computed(() => {
  if (!searchQuery.value) return rows.value
  const q = searchQuery.value.toLowerCase()
  return rows.value.filter(r =>
    r.name.toLowerCase().includes(q) ||
    (r.code && r.code.toLowerCase().includes(q)) ||
    (r.description && r.description.toLowerCase().includes(q))
  )
})

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除课程「${row.name}」吗？这将同时删除所有关联绑定。`, '警告', { type:'warning' })
    await deleteCourse(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) { /* 取消或失败 */ }
}

onMounted(loadData)
</script>

<style scoped>
.toolbar{display:flex;gap:10px;margin:16px 0}
</style>