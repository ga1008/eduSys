<template>
  <div class="course-list-page" v-loading="loading">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="text-large font-600 mr-3"> 我的课程 </span>
      </template>
    </el-page-header>

    <el-row :gutter="24" v-if="validCourses.length > 0" class="course-grid">
      <el-col
          v-for="(course, index) in validCourses"
          :key="course.id"
          :xs="24" :sm="12" :md="8" :lg="6"
          class="course-col"
      >
        <el-card
            shadow="hover"
            class="course-card"
            :body-style="{ padding: '0px' }"
            @click="gotoDetail(course.id)"
        >
          <div class="course-image-placeholder" :style="getPlaceholderStyle(index)">
            <el-icon class="course-icon-large">
              <Reading/>
            </el-icon>
          </div>
          <div class="course-content">
            <h3 class="course-title">{{ course.name }}</h3>
            <div class="course-meta">
              <span v-if="course.teacher_name">
                <el-icon><User/></el-icon> {{ course.teacher_name }}
              </span>
              <span v-else>
                <el-icon><User/></el-icon> 暂无教师信息
              </span>
            </div>
            <div class="course-meta">
              <span><el-icon><Coin/></el-icon> {{ course.credit }} 学分</span>
              <span><el-icon><Clock/></el-icon> {{ course.hours }} 学时</span>
            </div>
            <el-button type="primary" plain class="enter-course-btn" :icon="ArrowRightBold">
              进入课程
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && validCourses.length === 0" description="您目前还没有加入任何课程" class="empty-state">
      <el-button type="primary" @click="goToDashboard">返回首页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {fetchStudentCourses} from '@/api/student' //
import {ElMessage} from 'element-plus'
import {ArrowRightBold, Clock, Coin, Reading, User} from '@element-plus/icons-vue'

const router = useRouter() //

const courses = ref([]) //
const loading = ref(true) //

const placeholderColors = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C',
  '#5470c6', '#91cc75', '#fac858', '#ee6666',
  '#73c0de', '#3ba272', '#fc8452', '#9a60b4'
];

const getPlaceholderStyle = (index) => {
  return {
    backgroundColor: placeholderColors[index % placeholderColors.length]
  };
};

const loadCourses = async () => {
  loading.value = true
  try {
    const response = await fetchStudentCourses() //
    // API 返回的数据结构可能是 { results: [...] } 或直接是 [...]
    // 后端 StudentCourseViewSet 使用的是 ReadOnlyModelViewSet，默认情况下列表会分页并包含在 results 字段中
    // 如果后端没有分页，则 data 可能直接是数组
    if (response && response.data) {
      // 检查 response.data.results 是否为数组，如果不是，尝试 response.data 本身
      courses.value = Array.isArray(response.data.results) ? response.data.results :
          (Array.isArray(response.data) ? response.data : []);
    } else {
      courses.value = []
      ElMessage.warning('未获取到课程数据');
    }
  } catch (error) {
    console.error('加载课程列表失败:', error)
    ElMessage.error('加载课程列表失败，请稍后重试')
    courses.value = [] //
  } finally {
    loading.value = false //
  }
}

const validCourses = computed(() => { //
  return courses.value.filter(course =>
      course && typeof course === 'object' && course.id !== undefined && course.id !== null
  ).map(course => ({
    ...course,
    name: course.name || course.course_name || '未命名课程', //
    credit: course.credit ?? '-', // 使用 ?? 运算符提供默认值
    hours: course.hours ?? '-', // 使用 ?? 运算符提供默认值
    teacher_name: course.teacher_name || null // 确保 teacher_name 存在或为 null
  }));
})

const gotoDetail = (id) => { //
  router.push({name: 'StudentCourseDetail', params: {id}}) //
}

const goBack = () => {
  router.back()
}
const goToDashboard = () => {
  router.push({name: 'StudentHome'}); // 假设学生首页路由名为 StudentHome
}


onMounted(loadCourses)
</script>

<style scoped>
.course-list-page {
  padding: 24px;
  background-color: #f9fafb; /* 淡雅的背景色 */
}

.page-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.page-header .text-large {
  font-size: 20px;
  color: #303133;
}

.course-grid {
  margin-left: -12px !important; /* 抵消 gutter */
  margin-right: -12px !important;
}

.course-col {
  margin-bottom: 24px;
}

.course-card {
  border-radius: 12px; /* 更圆润的卡片 */
  overflow: hidden; /* 确保图片占位符的圆角生效 */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--el-box-shadow-light); /* 使用Element Plus的阴影变量 */
}

.course-image-placeholder {
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.course-icon-large {
  font-size: 60px;
  opacity: 0.8;
}

.course-content {
  padding: 18px;
}

.course-title {
  font-weight: 600;
  font-size: 17px;
  color: #303133;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis; /* 标题过长时显示省略号 */
}

.course-meta {
  color: #606266; /* 次要信息颜色 */
  font-size: 13px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 16px; /* meta项之间的间距 */
}

.course-meta .el-icon {
  margin-right: 5px;
  vertical-align: middle;
}

.enter-course-btn {
  width: 100%;
  margin-top: 12px;
}

.empty-state {
  margin-top: 40px;
}
</style>