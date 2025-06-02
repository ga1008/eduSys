<!-- HomeworkSubmissionList.vue -->
<template>
  <div class="submission-container">
    <el-page-header :content="hw.title" @back="$router.back()" />

    <!-- 筛选工具栏 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="search"
          placeholder="搜索学生/学号"
          class="filter-item"
          clearable
        />
        <el-select
          v-model="selectedCourse"
          placeholder="选择课程"
          class="filter-item"
          clearable
        >
          <el-option
            v-for="course in courses"
            :key="course.course_id"
            :label="course.course_name"
            :value="course.course_id"
          />
        </el-select>
        <el-select
          v-model="selectedClass"
          placeholder="选择班级"
          class="filter-item"
          clearable
        >
          <el-option
            v-for="cls in classes"
            :key="cls.class_id"
            :label="cls.class_name"
            :value="cls.class_id"
          />
        </el-select>
        <el-switch
          v-model="onlyUngraded"
          active-text="仅未批改"
          class="filter-item"
        />
      </div>
    </el-card>

    <el-card class="table-card">
      <!-- 提交列表 -->
      <el-table
        :data="filtered"
        stripe
        border
        v-loading="loading"
      >
        <el-table-column label="姓名" min-width="80">
          <template #default="{ row }">{{ row.student_name }}</template>
        </el-table-column>
        <el-table-column label="学号" min-width="120">
          <template #default="{ row }">{{ row.student_number }}</template>
        </el-table-column>
        <el-table-column label="班级" min-width="120">
          <template #default="{ row }">{{ row.class_name }}</template>
        </el-table-column>
        <el-table-column label="课程" min-width="120">
          <template #default="{ row }">{{ row.course_name }}</template>
        </el-table-column>
        <el-table-column label="提交时间" min-width="150">
          <template #default="{ row }">
            {{ dayjs(row.submit_time).format('YYYY-MM-DD HH:mm') }}
          </template>
        </el-table-column>
        <el-table-column label="分数" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getScoreTagType(row.score)"
              class="score-tag"
            >
              {{ row.score ?? '未批' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="100" fixed="right">
          <template #default="{ row }">
            <router-link :to="{ name:'TeacherHomeworkGrade', params:{
              subId: row.id,
              stuData: {
                name: row.student_name,
                number: row.student_number,
                class: row.class_name,
                course: row.course_name
              }
            } }">
              <el-button type="primary" size="small">
                {{ row.score === null ? '批改' : '查看' }}
              </el-button>
            </router-link>
              <el-button type="danger" size="small" @click="returnSubmission(row)" style="margin-left: 5px">
                退回
              </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-empty
      v-if="!loading && !filtered.length"
      description="暂无提交记录"
      class="empty-box"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import dayjs from 'dayjs'
import {fetchHomework, fetchHomeworkSubmissions, gradeSubmission} from '@/api/homeworks'
import { fetchTeacherCourseClasses } from '@/api/teachers'
import {ElMessage} from "element-plus";

const route = useRoute()
const hwId = route.params.hwId

// 数据状态
const hw = ref({})
const subs = ref([])
const courses = ref([])
const classes = ref([])
const loading = ref(false)

// 筛选条件
const search = ref('')
const selectedCourse = ref(null)
const selectedClass = ref(null)
const onlyUngraded = ref(false)

// 获取课程班级数据
const loadCourseClasses = async () => {
  const { data } = await fetchTeacherCourseClasses()

  // 提取唯一的课程
  const uniqueCourses = new Map()
  data.forEach(item => {
    uniqueCourses.set(item.course_id, {
      course_id: item.course_id,
      course_name: item.course_name
    })
  })
  courses.value = [...uniqueCourses.values()]

  // 提取唯一的班级
  const uniqueClasses = new Map()
  data.forEach(item => {
    uniqueClasses.set(item.class_id, {
      class_id: item.class_id,
      class_name: item.class_name
    })
  })
  classes.value = [...uniqueClasses.values()]
}

// 撤回提交
const returnSubmission = async (submission) => {
  try {
    await gradeSubmission(submission.id, {
      score: null,
      teacher_comment: '退回',
      is_returned: true
    })
    ElMessage.success('提交已撤回')
  } catch (error) {
    ElMessage.error('撤回提交失败，请稍后重试')
  }
}

// 过滤逻辑
const filtered = computed(() => {
  let data = subs.value

  if (selectedCourse.value) {
    data = data.filter(s => s.course_id === selectedCourse.value)
  }

  if (selectedClass.value) {
    data = data.filter(s => s.class_id === selectedClass.value)
  }

  if (onlyUngraded.value) {
    data = data.filter(s => s.score === null)
  }

  if (search.value) {
    const k = search.value.toLowerCase()
    data = data.filter(s =>
      (s.student_name || '').toLowerCase().includes(k) ||
      (s.student_number || '').includes(k)
    )
  }

  return data
})

const getScoreTagType = (score) => {
  if (score === null) return 'info'
  const max = hw.value.max_score || 100
  return score >= max * 0.8 ? 'success' : score >= max * 0.6 ? 'warning' : 'danger'
}

onMounted(async () => {
  loading.value = true
  try {
    await loadCourseClasses()
    hw.value = (await fetchHomework(hwId)).data
    subs.value = (await fetchHomeworkSubmissions(hwId)).data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.submission-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.filter-item {
  width: 200px;
}

.table-card {
  margin-bottom: 20px;
}

.score-tag {
  font-size: 14px;
  font-weight: 500;
}

.empty-box {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 30px 0;
  margin-top: 20px;
}

:deep(.el-table__row) {
  transition: all 0.2s;
}

:deep(.el-table__row:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
</style>