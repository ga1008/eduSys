<template>
  <div class="course-detail-page" v-loading="loading">
    <el-page-header @back="goBackToList" class="page-header">
      <template #content>
        <span class="text-large font-600 mr-3">{{ course?.course_name || '课程详情' }}</span>
      </template>
      <template #extra v-if="course">
        <div class="header-actions">
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
      <el-tabs v-model="activeTab" class="course-tabs" @tab-change="handleTabChange">

        <el-tab-pane label="课程信息" name="info">
          <el-descriptions :column="isMobile ? 1 : 2" border class="course-descriptions">
            <el-descriptions-item label="任课教师">{{ course.teacher_name || '暂无信息' }}</el-descriptions-item>
            <el-descriptions-item label="开课日期">{{ formatDate(course.start_date) }}</el-descriptions-item>
            <el-descriptions-item label="结课日期">{{ formatDate(course.end_date) }}</el-descriptions-item>
            <el-descriptions-item label="课程描述" :span="2" v-if="course.course_description">
              <div class="description-content" v-html="course.course_description || '暂无描述'"></div>
            </el-descriptions-item>
            <el-descriptions-item label="推荐教材" :span="2" v-if="course.textbook">
              <div v-html="course.textbook"></div>
            </el-descriptions-item>
            <el-descriptions-item label="教学大纲" :span="2" v-if="course.syllabus">
              <div v-html="course.syllabus"></div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="课程作业" name="assignments">
          <div v-loading="assignmentsLoading">
            <el-empty v-if="assignments.length === 0" description="老师还没布置作业哦"></el-empty>
            <el-timeline v-else>
              <el-timeline-item
                  v-for="item in assignments"
                  :key="item.id"
                  :timestamp="`截止时间: ${formatDate(item.due_date, 'YYYY-MM-DD HH:mm')}`"
                  placement="top"
                  :type="getAssignmentStatusType(item)"
              >
                <el-card>
                  <h4>{{ item.title }}</h4>
                  <p>状态:
                    <el-tag size="small" :type="getAssignmentStatusType(item)">{{
                        getAssignmentStatusText(item)
                      }}
                    </el-tag>
                  </p>
                  <p v-if="item.submitted && item.score !== null">得分: <strong>{{ item.score }}</strong> /
                    {{ item.max_score }}</p>
                  <el-button type="primary" size="small" @click="viewAssignment(item.id)">查看与提交</el-button>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>

        <el-tab-pane label="学习资料" name="materials">
          <div v-loading="materialsLoading">
            <el-empty v-if="materials.length === 0" description="老师还没上传资料哦"></el-empty>
            <el-table :data="materials" stripe v-else>
              <el-table-column prop="title" label="资料名称"></el-table-column>
              <el-table-column prop="material_type" label="类型" width="120">
                <template #default="scope">
                  <el-tag>{{ scope.row.material_type_display }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="upload_time" label="上传时间" width="180">
                <template #default="scope">{{ formatDate(scope.row.upload_time) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="scope">
                  <el-button type="primary" link @click="downloadMaterial(scope.row)">下载</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="在线研讨" name="chatroom">
          <ChatRoom v-if="activeTab === 'chatroom' && course.chatroom_id" :room-id="course.chatroom_id"/>
          <el-empty v-else-if="activeTab === 'chatroom'" description="该课程未开启聊天室功能"/>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-empty v-else-if="!loading" description="课程信息加载失败或不存在。">
      <el-button type="primary" @click="goBackToList">返回课程列表</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {
  fetchStudentCourseDetail,
  fetchCourseAssignments,
  fetchCourseMaterials,
  downloadCourseMaterial
} from '@/api/student';
import {Clock, Coin} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import ChatRoom from '@/components/ChatRoom.vue'; // 引入聊天室组件

const route = useRoute();
const router = useRouter();

const course = ref(null);
const loading = ref(true);
const activeTab = ref('info');

const assignments = ref([]);
const assignmentsLoading = ref(false);

const materials = ref([]);
const materialsLoading = ref(false);

const isMobile = computed(() => window.innerWidth < 768);

const loadCourseDetail = async () => {
  loading.value = true;
  try {
    const response = await fetchStudentCourseDetail(route.params.id);
    course.value = response.data;
    // 页面加载后默认请求第一个tab的数据
    if (activeTab.value === 'info') {
      // info的数据已在course中
    } else {
      handleTabChange(activeTab.value);
    }
  } catch (e) {
    ElMessage.error('加载课程详情失败');
  } finally {
    loading.value = false;
  }
};

const loadAssignments = async () => {
  if (assignments.value.length > 0) return; // 避免重复加载
  assignmentsLoading.value = true;
  try {
    const response = await fetchCourseAssignments(route.params.id);
    assignments.value = response.data;
  } catch (error) {
    ElMessage.error('加载作业列表失败');
  } finally {
    assignmentsLoading.value = false;
  }
};

const loadMaterials = async () => {
  if (materials.value.length > 0) return;
  materialsLoading.value = true;
  try {
    const response = await fetchCourseMaterials(route.params.id);
    materials.value = response.data;
  } catch (error) {
    ElMessage.error('加载资料列表失败');
  } finally {
    materialsLoading.value = false;
  }
};

const handleTabChange = (tabName) => {
  if (tabName === 'assignments') {
    loadAssignments();
  } else if (tabName === 'materials') {
    loadMaterials();
  }
};

const downloadMaterial = async (material) => {
  try {
    const response = await downloadCourseMaterial(material.id);
    const blob = new Blob([response.data]);
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(blob);
    link.download = material.title; // 使用资料标题作为文件名
    link.click();
    window.URL.revokeObjectURL(link.href);
  } catch (error) {
    ElMessage.error('下载失败');
  }
};

const getAssignmentStatusText = (item) => {
  if (item.is_returned) return '已退回';
  if (item.score !== null) return '已批改';
  if (item.submitted) return '已提交';
  if (dayjs().isAfter(dayjs(item.due_date))) return '已截止';
  return '待提交';
};

const getAssignmentStatusType = (item) => {
  if (item.score !== null) return 'success';
  if (item.is_returned) return 'danger';
  if (item.submitted) return 'primary';
  if (dayjs().isAfter(dayjs(item.due_date))) return 'info';
  return 'warning';
};

const viewAssignment = (assignmentId) => {
  router.push({name: 'StudentAssignmentSubmit', params: {id: assignmentId}});
};

const formatDate = (dateStr, format = 'YYYY-MM-DD') => {
  return dateStr ? dayjs(dateStr).format(format) : '待定';
};

const goBackToList = () => {
  router.push({name: 'StudentCourses'});
};

onMounted(() => {
  loadCourseDetail();
});
</script>

<style scoped>
/* 样式与之前类似，可以微调以增强美感 */
.course-detail-page {
  padding: 24px;
  background-color: #f9fafb;
}

.page-header {
  margin-bottom: 24px;
}

.course-main-card {
  border: none;
}

.el-timeline {
  padding-left: 10px;
}

.el-card {
  border-radius: 8px;
}

.description-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}
</style>