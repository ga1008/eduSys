<template>
  <div class="course-detail-page" v-loading="loading">
    <el-page-header @back="goBackToList" class="page-header">
      <template #content>
        <span class="text-large font-600 mr-3" v-if="course">{{ course.course_name }}</span>
        <span class="text-large font-600 mr-3" v-else>课程详情</span>
      </template>
      <template #extra>
        <div class="header-actions" v-if="course">
          <el-tag type="success" effect="light" size="large" round class="mr-2">
            <el-icon>
              <Coin/>
            </el-icon>
            {{ course.credit }} 学分
          </el-tag>
          <el-tag type="info" effect="light" size="large" round>
            <el-icon>
              <Clock/>
            </el-icon>
            {{ course.hours }} 学时
          </el-tag>
        </div>
      </template>
    </el-page-header>

    <el-card v-if="course" class="course-main-card" shadow="never">
      <el-tabs v-model="activeTab" class="course-tabs">
        <el-tab-pane label="课程信息" name="info">
          <el-descriptions :column="isMobile ? 1 : 2" border class="course-descriptions">
            <el-descriptions-item label-class-name="desc-label" label="课程名称">
              {{ course.course_name }}
            </el-descriptions-item>
            <el-descriptions-item label-class-name="desc-label" label="任课教师">
              {{ course.teacher_name || '暂无信息' }}
            </el-descriptions-item>

            <el-descriptions-item label-class-name="desc-label" label="开课日期" v-if="course.start_date">
              {{ formatDate(course.start_date) }}
            </el-descriptions-item>
            <el-descriptions-item label-class-name="desc-label" label="结课日期" v-if="course.end_date">
              {{ formatDate(course.end_date) }}
            </el-descriptions-item>

            <el-descriptions-item label-class-name="desc-label" label="课程描述" :span="isMobile ? 1: 2"
                                  v-if="course.course_description">
              <div class="description-content" v-html="course.course_description || '暂无描述'"></div>
            </el-descriptions-item>
            <el-descriptions-item label-class-name="desc-label" label="推荐教材" :span="isMobile ? 1: 2"
                                  v-if="course.textbook">
              <div class="description-content" v-html="course.textbook || '暂无教材信息'"></div>
            </el-descriptions-item>
            <el-descriptions-item label-class-name="desc-label" label="教学大纲" :span="isMobile ? 1: 2"
                                  v-if="course.syllabus">
              <div class="syllabus-content" v-html="course.syllabus || '暂无教学大纲'"></div>
            </el-descriptions-item>
            <el-descriptions-item label-class-name="desc-label" label="教学进度" :span="isMobile ? 1: 2"
                                  v-if="course.progress">
              <div class="description-content" v-html="course.progress || '暂无教学进度'"></div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="课程作业" name="assignments">
          <router-view name="StudentCourseAssignmentsView"></router-view>
        </el-tab-pane>

        <el-tab-pane label="学习资料" name="materials">
          <router-view name="StudentCourseMaterialsView"></router-view>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-empty v-else-if="!loading" description="课程信息加载失败或不存在。" class="empty-state">
      <el-button type="primary" @click="goBackToList">返回课程列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
// 在组件卸载前移除事件监听器
import {computed, onBeforeUnmount, onMounted, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {fetchStudentCourseDetail} from '@/api/student' //
import {Clock, Coin} from '@element-plus/icons-vue'
import dayjs from 'dayjs' //

const route = useRoute() //
const router = useRouter() //

const course = ref(null) //
const loading = ref(true) //
const activeTab = ref('info') // 默认激活的标签页

// 简单的响应式判断
const windowWidth = ref(window.innerWidth);
const isMobile = computed(() => windowWidth.value < 768);
const updateWidth = () => {
  windowWidth.value = window.innerWidth;
};

const loadCourseDetail = async () => {
  const id = route.params.id
  if (!id) {
    ElMessage.warning('未指定课程ID')
    router.replace({name: 'StudentCourses'}) //
    return
  }
  loading.value = true //
  try {
    const response = await fetchStudentCourseDetail(id) //
    if (response && response.data) {
      course.value = response.data //
    } else {
      course.value = null;
      ElMessage.error('课程信息不存在或已下架')
      // router.replace({ name: 'StudentCourses' }) // 避免在加载失败时立即跳转，让用户看到空状态提示
    }
  } catch (e) {
    console.error('加载课程详情失败:', e)
    ElMessage.error('加载课程详情失败，请稍后重试')
    course.value = null; // 确保加载失败时course为null，以显示ElEmpty
    // router.replace({ name: 'StudentCourses' }) //
  } finally {
    loading.value = false //
  }
}

const formatDate = (dateStr, format = 'YYYY年MM月DD日') => {
  return dateStr ? dayjs(dateStr).format(format) : '待定';
}

const goBackToList = () => {
  router.push({name: 'StudentCourses'}) // 跳转回课程列表页面
}

// 监听路由变化，切换标签页
watch(
    () => route.name,
    (newName) => {
      if (newName === 'StudentCourseAssignments') {
        activeTab.value = 'assignments';
      } else if (newName === 'StudentCourseMaterials') {
        activeTab.value = 'materials';
      } else if (newName === 'StudentCourseDetail') { // 如果是主详情路由，默认显示info
        activeTab.value = 'info';
      }
    },
    {immediate: true} // 立即执行一次以设置初始标签
);

// 监听标签页变化，更新路由 (如果希望标签页切换也改变URL)
watch(activeTab, (newTab) => {
  if (newTab === 'info' && route.name !== 'StudentCourseDetail') {
    // 如果当前不在主详情路由，且要切换到info，则导航到主详情路由
    router.push({name: 'StudentCourseDetail', params: {id: route.params.id}});
  } else if (newTab === 'assignments' && route.name !== 'StudentCourseAssignments') {
    router.push({name: 'StudentCourseAssignments', params: {id: route.params.id}});
  } else if (newTab === 'materials' && route.name !== 'StudentCourseMaterials') {
    router.push({name: 'StudentCourseMaterials', params: {id: route.params.id}});
  }
});


onMounted(() => {
  loadCourseDetail()
  window.addEventListener('resize', updateWidth);
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateWidth);
});

</script>

<style scoped>
.course-detail-page {
  padding: 24px;
  background-color: #f9fafb;
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

.header-actions .el-tag {
  font-size: 14px;
}

.header-actions .el-icon {
  margin-right: 4px;
  vertical-align: middle;
}

.course-main-card {
  border-radius: 8px;
  border: none; /* 移除卡片边框，让tabs撑满 */
}

.course-tabs {
  margin: -1px; /* 微调以更好地与卡片融合 */
}

.course-tabs :deep(.el-tabs__header) {
  margin-bottom: 0; /* 移除tabs头部的下边距 */
}

.course-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none; /* 移除tabs底部的默认线条 */
}

.course-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  padding: 0 20px !important; /* 增加tab的内边距 */
}

.course-tabs :deep(.el-tab-pane) {
  padding: 20px; /* 为标签页内容区添加内边距 */
}


.course-descriptions {
  margin-top: 10px;
}

.course-descriptions :deep(.desc-label) {
  font-weight: 500 !important;
  color: #555 !important;
  background-color: #fafafa !important;
  min-width: 100px; /* 确保标签有足够宽度 */
  text-align: right !important;
  padding-right: 12px !important;
}

.course-descriptions :deep(.el-descriptions__content) {
  color: #333;
}

.description-content, .syllabus-content {
  line-height: 1.8;
  color: #454545;
  white-space: pre-wrap; /* 保留换行和空格 */
}

.empty-state {
  margin-top: 40px;
}

/* 对于嵌套路由的内容区，如果需要特定样式 */
:deep(.el-tab-pane router-view) {
  /* 例如，可以添加一些内边距 */
  /* padding-top: 16px; */
}

.mr-2 {
  margin-right: 8px;
}
</style>