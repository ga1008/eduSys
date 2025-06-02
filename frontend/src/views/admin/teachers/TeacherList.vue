<!--教师列表页-->
<!-- 教师列表页 -->
<template>
  <div>
    <h2>教师管理</h2>

    <div class="toolbar">
      <el-button type="primary" @click="router.push('/admin/teachers/new')">新增教师</el-button>
      <el-input v-model="searchQuery" placeholder="搜索教师..." clearable style="width:260px" />
    </div>

    <el-table :data="filteredTeachers" border v-loading="loading" style="width:100%">
      <el-table-column prop="id" label="ID" width="80"/>
      <el-table-column prop="teacher_number" label="工号" width="130"/>
      <el-table-column prop="name" label="姓名" width="120"/>
      <el-table-column prop="gender" label="性别" width="80">
        <template #default="scope">
          {{ formatGender(scope.row.gender) }}
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱"/>
      <el-table-column prop="phone" label="电话" width="120"/>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" type="primary" @click="router.push(`/admin/teachers/${scope.row.id}/edit`)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchTeachers, deleteTeacher } from '@/api/teachers'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const teachers = ref([])
const loading = ref(false)
const searchQuery = ref('')

// 加载教师列表数据
const loadTeachers = async () => {
  loading.value = true
  try {
    const { data } = await fetchTeachers()
    teachers.value = data
  } catch (error) {
    ElMessage.error('获取教师列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 格式化性别显示
const formatGender = (gender) => {
  const genderMap = {
    'M': '男',
    'F': '女',
    'O': '其他'
  }
  return genderMap[gender] || '未知'
}

// 搜索过滤
const filteredTeachers = computed(() => {
  if (!searchQuery.value) return teachers.value
  const query = searchQuery.value.toLowerCase()
  return teachers.value.filter(teacher =>
    (teacher.name && teacher.name.toLowerCase().includes(query)) ||
    (teacher.teacher_number && teacher.teacher_number.toLowerCase().includes(query)) ||
    (teacher.email && teacher.email.toLowerCase().includes(query)) ||
    (teacher.phone && teacher.phone.toLowerCase().includes(query))
  )
})

// 删除教师
const handleDelete = async (teacher) => {
  try {
    await ElMessageBox.confirm(
      `确定删除教师「${teacher.name || teacher.teacher_number}」吗？这可能影响相关课程安排。`,
      '警告',
      { type: 'warning' }
    )
    await deleteTeacher(teacher.id)
    ElMessage.success('删除成功')
    await loadTeachers()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(e)
    }
  }
}

onMounted(loadTeachers)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}
</style>