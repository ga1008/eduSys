<template>
  <div class="homework-page">
    <el-card class="filter-card">
      <div class="filter-container">
        <div class="selector-wrapper">
          <span class="label">课程班级：</span>
          <el-select
            v-model="selectedId"
            filterable
            placeholder="选择课程班级"
            class="class-select"
            @change="onClassChange">
            <el-option
              v-for="cc in courseClasses"
              :key="cc.id"
              :value="cc.id"
              :label="`${cc.course_name}（${cc.class_name}）`"/>
          </el-select>
        </div>

        <el-button
          type="primary"
          :disabled="!selectedId"
          class="create-btn"
          @click="createHomework">
          <el-icon><Plus/></el-icon>
          新建作业
        </el-button>
      </div>
    </el-card>

    <!-- Homework table -->
    <el-table
      v-loading="loading"
      :data="homeworks"
      stripe
      border
      class="hw-table">
      <el-table-column label="作业标题" min-width="150">
        <template #default="scope">
          <el-tag :type="summitMarkedType(scope.row)" size="small" style="cursor: pointer; margin-right: 8px" @click="pushToHomeworkSubmissions(scope.row)">
            {{ scope.row.marked_count }} / {{ scope.row.submit_count }}
          </el-tag>

          <el-text type="primary" style="cursor: pointer; font-size: large;" @click="pushToHomeworkSubmissions(scope.row)">
            {{ scope.row.title }}
          </el-text>
          <el-tag type="info" size="small" style="margin-left: 8px;">
            {{ formatDate(scope.row.deploy_date) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="截止日期" min-width="100">
        <template #default="scope">
          {{ formatDate(scope.row.due_date || scope.row.deadline) }}
          <el-button
            v-if="scope.row.due_date || scope.row.deadline"
            type="warning"
            size="small"
            @click="addOneDay(scope.row)">
            +1天
          </el-button>
          <el-button
            v-if="scope.row.due_date || scope.row.deadline"
            type="warning"
            size="small"
            @click="addOneDay(scope.row, 7)">
            +1周
          </el-button>
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="操作">
        <template #default="scope">

          <div class="button-group">
            <router-link :to="{ name:'TeacherHomeworkSubmissions', params:{ hwId: scope.row.id } }">
              <el-button size="small" type="success">查看提交</el-button>
            </router-link>
            <el-button
              size="small"
              type="primary"
              style="margin-left: 10px"
              @click="editHomework(scope.row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteHomework(scope.row)">删除</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !homeworks.length" description="没有布置作业呢，来点吧"/>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {fetchTeacherCourseClasses, fetchUngradedHomeworks} from '@/api/teachers'
import { fetchHomeworks, updateHomework, deleteHomework as apiDel } from '@/api/homeworks'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const courseClasses = ref([])
const homeworks = ref([])
const selectedId = ref(null)

/* 改进的日期格式化函数 */
function formatDate(dateString) {
  if (!dateString) return '未设置'

  try {
    const date = new Date(dateString)

    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.error('无效日期:', dateString)
      return '日期格式错误'
    }

    // 获取星期几（0-6，0表示星期日）
    const day = date.getDay()
    // 中文星期映射
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']

    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}（星期${weekDays[day]}） ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } catch (error) {
    console.error('格式化日期出错:', error)
    return '日期格式错误'
  }
}

function summitMarkedType(row) {
  if (row.marked_count < row.submit_count) return 'warning'
  return 'success'
}

function pushToHomeworkSubmissions(row) {
  router.push({ name: 'TeacherHomeworkSubmissions', params: { hwId: row.id } })
}

function addOneDay(row, days = 1) {
  if (!row.due_date) {
    ElMessage.error('没有设置截止日期，无法加一天')
    return
  }

  const newDate = new Date(row.due_date)
  newDate.setDate(newDate.getDate() + days)

  // 更新作业的截止日期 格式化为 YYYY-MM-DD HH:mm:ss，后面的时间沿用原来的
  row.due_date = newDate
  // 这里可以调用 API 更新作业的截止日期
  updateHomework(row.id, { due_date: newDate })
    .then(() => {
      ElMessage.success('截止日期更新成功')
      loadHomeworks(selectedId.value)
    })
    .catch(error => {
      console.error('更新截止日期失败:', error)
      ElMessage.error('更新截止日期失败')
    })
}

// 其余函数保持不变
async function loadCourseClasses() {
  const { data } = await fetchTeacherCourseClasses()
  courseClasses.value = [...data].sort(
    (a, b) => new Date(b.updated_at || b.start_date) - new Date(a.updated_at || a.start_date)
  )
}

async function loadHomeworks(id) {
  loading.value = true
  try {
    const { data } = await fetchHomeworks(id)
    homeworks.value = data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadCourseClasses()
  const id = route.params.id ? Number(route.params.id) : courseClasses.value[0]?.id
  if (id) {
    selectedId.value = id
    router.replace({ params: { id } })
  };

  await fetchUngradedHomeworks()
    .then((res) => {
      console.log("未批改作业:" + res.data)
    })
    .catch(error => {
      console.error('加载未批改作业失败:', error)
      ElMessage.error('加载未批改作业失败，请稍后重试')
    })

})

watch(selectedId, id => id && loadHomeworks(id))

/* --------------- actions --------------- */
function onClassChange(id) {
  router.push({ params: { id } })
}

function createHomework() {
  router.push(`/teacher/courses/homeworks/${selectedId.value}/create`)
}

function editHomework(row) {
  router.push(`/teacher/courses/homeworks/${selectedId.value}/edit/${row.id}`)
}

function deleteHomework(row) {
  ElMessageBox.confirm('确定删除该作业吗？', '提示', { type: 'warning' })
    .then(async () => {
      await apiDel(row.id)
      ElMessage.success('删除成功')
      loadHomeworks(selectedId.value)
    })
}
</script>

<style scoped>
.homework-page {
  padding: 24px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selector-wrapper {
  display: flex;
  align-items: center;
  flex: 1;
}

.label {
  font-size: 14px;
  margin-right: 10px;
  white-space: nowrap;
  color: #606266;
}

.class-select {
  width: 320px;
}

.create-btn {
  margin-left: 20px;
}

.hw-table {
  width: 100%;
}

.button-group {
  display: flex;
  gap: 8px;
}
</style>