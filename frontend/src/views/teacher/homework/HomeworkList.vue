<template>
  <div class="homework-page">
    <el-card class="filter-card" shadow="never">
      <div class="filter-container">
        <div class="selector-wrapper">
          <span class="label">课程班级：</span>
          <el-select
              v-model="selectedId"
              filterable
              placeholder="选择或搜索课程班级"
              class="class-select"
              @change="onClassChange"
              loading-text="加载中..."
              :loading="courseClassesLoading"
          >
            <el-option
                v-for="cc in courseClasses"
                :key="cc.id"
                :value="cc.id"
                :label="`${cc.course_name}（${cc.class_name}） - ${cc.teacher_name}`"
            />
          </el-select>
        </div>

        <el-button
            type="primary"
            :disabled="!selectedId"
            class="create-btn"
            @click="createHomework"
        >
          <el-icon>
            <Plus/>
          </el-icon>
          新建作业
        </el-button>
      </div>
    </el-card>

    <el-table
        v-loading="loading"
        :data="homeworks"
        stripe
        border
        class="hw-table"
        empty-text="暂无作业数据"
    >
      <el-table-column label="作业标题" min-width="120">
        <template #default="scope">
          <div class="title-cell">
            <el-tag :type="summitMarkedType(scope.row)" size="small"
                    style="cursor: pointer; margin-right: 8px; flex-shrink: 0;"
                    @click="pushToHomeworkSubmissions(scope.row)">
              {{ scope.row.marked_count }} | {{ scope.row.ai_marked_count }} / {{ scope.row.submit_count }}
            </el-tag>
            <el-tooltip :content="scope.row.title" placement="top">
              <span class="homework-title" @click="pushToHomeworkSubmissions(scope.row)">
                {{ scope.row.title }}
              </span>
            </el-tooltip>
            <el-tag type="info" size="small" style="margin-left: 8px; flex-shrink: 0;">
              {{ formatDateShort(scope.row.deploy_date) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="截止日期" align="center">
        <template #default="scope">
          <div>{{ formatDate(scope.row.due_date || scope.row.deadline) }}</div>
          <div v-if="scope.row.due_date || scope.row.deadline" style="margin-top: 5px;">
            <el-button-group size="small">
              <el-button type="warning" plain @click="addDueDate(scope.row, 1)">+1天</el-button>
              <el-button type="warning" plain @click="addDueDate(scope.row, 7)">+1周</el-button>
            </el-button-group>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="AI辅助" width="120" align="center">
        <template #default="scope">
          <el-tooltip :content="scope.row.ai_grading_enabled ? '点击关闭AI辅助批改' : '点击开启AI辅助批改'"
                      placement="top">
            <el-switch
                v-model="scope.row.ai_grading_enabled"
                @change="toggleAiGrading(scope.row)"
                size="small"
                inline-prompt
                active-text="开"
                inactive-text="关"
            />
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column fixed="right" label="操作" align="center">
        <template #default="scope">
          <div class="button-group">
            <el-button size="small" type="success" plain @click="pushToHomeworkSubmissions(scope.row)">
              <el-icon>
                <View/>
              </el-icon>
              查看提交
            </el-button>
            <el-button
                size="small"
                type="primary"
                plain
                @click="editHomework(scope.row)"
            >
              <el-icon>
                <Edit/>
              </el-icon>
              编辑
            </el-button>
            <el-button
                v-if="scope.row.ai_grading_enabled"
                size="small"
                type="primary"
                @click="editAiPrompt(scope.row)"
            >
              <el-icon>
                <Setting/>
              </el-icon>
              AI设置
            </el-button>
            <el-popconfirm
                title="确定删除该作业吗？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                width="200"
                @confirm="confirmDeleteHomework(scope.row)"
            >
              <template #reference>
                <el-button size="small" type="danger" plain>
                  <el-icon>
                    <Delete/>
                  </el-icon>
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && !homeworks.length && selectedId"
              description="该课程班级下还没有布置作业，快去新建一个吧！"/>
    <el-empty v-if="!loading && !selectedId" description="请先选择一个课程班级以查看作业。"/>

  </div>
</template>

<script setup>
import {ref, onMounted, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {Plus, Edit, Delete, View, Setting} from '@element-plus/icons-vue' // Import Setting icon
import {ElMessage, ElMessageBox} from 'element-plus'
import {fetchTeacherCourseClasses} from '@/api/teachers' // fetchUngradedHomeworks 已移除，若需要可恢复
import {fetchHomeworks, updateHomework, deleteHomework as apiDel} from '@/api/homeworks'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const courseClassesLoading = ref(false)
const courseClasses = ref([])
const homeworks = ref([])
const selectedId = ref(route.params.id ? Number(route.params.id) : null)


function formatDateShort(dateString) {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '日期错误';
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
  } catch (e) {
    return '日期错误';
  }
}

function formatDate(dateString) {
  if (!dateString) return '未设置';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      console.error('无效日期:', dateString);
      return '日期格式错误';
    }
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} (周${weekDays[date.getDay()]}) ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  } catch (error) {
    console.error('格式化日期出错:', error);
    return '日期格式错误';
  }
}

function summitMarkedType(row) {
  if (row.submit_count === 0) return 'info';
  if (row.ai_marked_count === row.submit_count) return 'primary';
  if (row.marked_count < row.submit_count) return 'warning';
  return 'success';
}

function pushToHomeworkSubmissions(row) {
  router.push({name: 'TeacherHomeworkSubmissions', params: {hwId: row.id}});
}

async function addDueDate(row, days = 1) {
  if (!row.due_date) {
    ElMessage.error('没有设置截止日期，无法调整');
    return;
  }
  const originalDate = new Date(row.due_date);
  const newDate = new Date(originalDate);
  newDate.setDate(newDate.getDate() + days);

  try {
    await updateHomework(row.id, {due_date: newDate.toISOString()}); // 发送 ISO 格式字符串
    ElMessage.success('截止日期更新成功');
    // 局部更新数据，避免重新加载整个列表
    const index = homeworks.value.findIndex(hw => hw.id === row.id);
    if (index !== -1) {
      homeworks.value[index].due_date = newDate.toISOString();
    }
  } catch (error) {
    console.error('更新截止日期失败:', error);
    ElMessage.error('更新截止日期失败: ' + (error.response?.data?.detail || error.message));
  }
}

async function loadCourseClasses() {
  courseClassesLoading.value = true;
  try {
    const {data} = await fetchTeacherCourseClasses();
    courseClasses.value = [...data].sort(
        (a, b) => (b.id - a.id) // 简单按ID降序，可以根据需要调整
    );
    // 如果当前selectedId不在加载的课程班级列表中，或者之前没有selectedId，则尝试设置默认值
    if (courseClasses.value.length > 0 && (!selectedId.value || !courseClasses.value.find(cc => cc.id === selectedId.value))) {
      if (!selectedId.value) { // 只有当selectedId完全未被设置时（例如直接访问基础URL）
        selectedId.value = courseClasses.value[0].id;
        // router.replace({ params: { id: selectedId.value } }); // 更新URL
      }
    } else if (courseClasses.value.length === 0) {
      selectedId.value = null; // 没有课程班级可选
    }

  } catch (error) {
    console.error('加载课程班级失败:', error);
    ElMessage.error('加载课程班级列表失败');
  } finally {
    courseClassesLoading.value = false;
  }
}

async function loadHomeworks(id) {
  if (!id) {
    homeworks.value = [];
    return;
  }
  loading.value = true;
  try {
    const {data} = await fetchHomeworks(id); // API应支持通过 course_class ID 筛选
    homeworks.value = data;
  } catch (error) {
    console.error('加载作业列表失败:', error);
    ElMessage.error('加载作业列表失败');
    homeworks.value = []; // 出错时清空列表
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadCourseClasses();
  // 如果 selectedId 仍然为 null (路由中没有，默认也没设置成功), 且有课程班级，则设置
  if (selectedId.value === null && courseClasses.value.length > 0) {
    selectedId.value = courseClasses.value[0].id;
  }
  // 只有在 selectedId 有效的情况下才加载作业，并在 URL 中同步它
  if (selectedId.value) {
    if (String(route.params.id) !== String(selectedId.value)) { // 避免不必要的替换
      router.replace({name: 'TeacherCourseHomeworks', params: {id: selectedId.value}});
    }
    await loadHomeworks(selectedId.value);
  }
});

// 监听 selectedId 的变化，当它变化时加载新的作业列表并更新路由（如果路由与selectedId不一致）
watch(selectedId, (newId, oldId) => {
  if (newId && newId !== oldId) { // 确保ID有效且发生变化
    if (String(route.params.id) !== String(newId)) {
      router.push({name: 'TeacherCourseHomeworks', params: {id: newId}}); // 使用push以便用户可以回退
    }
    loadHomeworks(newId);
  } else if (!newId) { // 如果 newId 是 null 或 undefined
    homeworks.value = []; // 清空作业列表
  }
});

// 监听路由参数变化，确保 selectedId 与路由同步
watch(() => route.params.id, (newRouteId) => {
  const idNum = newRouteId ? Number(newRouteId) : null;
  if (idNum !== selectedId.value) {
    selectedId.value = idNum;
    // selectedId 的 watch 会自动触发 loadHomeworks
  }
});


/* --------------- actions --------------- */
function onClassChange(id) {
  // selectedId 会通过 watch 更新路由和加载数据
  selectedId.value = id;
}

function createHomework() {
  if (!selectedId.value) {
    ElMessage.warning('请先选择一个课程班级');
    return;
  }
  router.push({name: 'TeacherCourseHomeworkCreate', params: {id: selectedId.value}});
}

function editHomework(row) {
  router.push({name: 'TeacherCourseHomeworkEdit', params: {id: selectedId.value, homeworkId: row.id}});
}

async function confirmDeleteHomework(row) {
  try {
    await apiDel(row.id);
    ElMessage.success('删除成功');
    // 重新加载当前选中课程班级的作业列表
    if (selectedId.value) {
      loadHomeworks(selectedId.value);
    }
  } catch (error) {
    console.error('删除作业失败:', error);
    ElMessage.error('删除作业失败: ' + (error.response?.data?.detail || error.message));
  }
}

// 新增：切换AI批改状态
async function toggleAiGrading(row) {
  const originalState = !row.ai_grading_enabled; // 记录切换前的状态，以便失败时恢复
  try {
    await updateHomework(row.id, {ai_grading_enabled: row.ai_grading_enabled});
    ElMessage.success(`AI辅助批改已成功${row.ai_grading_enabled ? '启用' : '禁用'}`);
    if (row.ai_grading_enabled && !row.ai_grading_prompt) { // 后端返回的 homeworks 数据需要包含 ai_grading_prompt
      ElMessage.info('AI批改已启用，建议点击“AI设置”配置详细的提示词。');
    }
  } catch (error) {
    ElMessage.error('切换AI批改状态失败');
    // 状态切换失败，恢复UI上的开关状态
    row.ai_grading_enabled = originalState;
    console.error("Toggle AI grading error:", error.response || error);
  }
}

// 新增：编辑AI提示词的导航
function editAiPrompt(row) {
  router.push({
    name: 'TeacherCourseHomeworkEdit',
    params: {id: selectedId.value, homeworkId: row.id},
    query: {focus_ai: 'true'}
  });
}

</script>

<style scoped>
.homework-page {
  padding: 20px;
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
  flex-grow: 1; /* 让选择器部分占据更多空间 */
  margin-right: 20px; /* 与按钮保持距离 */
}

.label {
  font-size: 14px;
  margin-right: 10px;
  white-space: nowrap;
  color: #606266;
}

.class-select {
  width: 100%; /* 自动适应父容器 */
  max-width: 400px; /* 最大宽度限制 */
}

.create-btn {
  flex-shrink: 0; /* 防止按钮被压缩 */
}

.hw-table {
  width: 100%;
}

.title-cell {
  display: flex;
  align-items: center;
}

.homework-title {
  cursor: pointer;
  color: var(--el-color-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-grow: 1;
  min-width: 0; /* Important for text-overflow to work in flex item */
}

.homework-title:hover {
  text-decoration: underline;
}

.button-group {
  display: flex;
  flex-wrap: nowrap; /* 确保按钮在一行 */
  gap: 8px; /* 按钮之间的间距 */
  align-items: center; /* 垂直居中对齐 */
}

.button-group .el-button, .button-group .el-switch {
  margin-left: 0 !important; /* 覆盖Element Plus可能的默认margin */
}

.el-table-column .cell { /* 确保单元格内容能正常显示 */
  display: flex;
  align-items: center;
}
</style>