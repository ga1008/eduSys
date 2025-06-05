<template>
  <div class="assignment-list-container p-6">
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold">我的作业</h1>
      <div class="filters">
        <el-radio-group v-model="statusFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="pending">待提交</el-radio-button>
          <el-radio-button label="submitted">已提交</el-radio-button>
          <el-radio-button label="overdue">已截止</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton animated :rows="5"/>
      <div class="text-center mt-4 text-gray-400">正在加载课程和作业...</div>
    </div>

    <el-result
        v-else-if="error"
        icon="error"
        :title="error"
        sub-title="请稍后重试或联系管理员">
      <template #extra>
        <el-button type="primary" @click="loadData">重新加载</el-button>
      </template>
    </el-result>

    <el-empty
        v-else-if="courses.length === 0"
        description="暂无课程"
        class="my-8">
    </el-empty>

    <div v-else class="courses-summary mb-6">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="hover" class="summary-card bg-blue-50">
            <div class="summary-value">{{ totalCourses }}</div>
            <div class="summary-label">总课程数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="summary-card bg-green-50">
            <div class="summary-value">{{ totalAssignments }}</div>
            <div class="summary-label">总作业数</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="summary-card bg-orange-50">
            <div class="summary-value">{{ pendingAssignments }}</div>
            <div class="summary-label">待提交作业</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="summary-card bg-red-50">
            <div class="summary-value">{{ overdueAssignments }}</div>
            <div class="summary-label">已截止作业</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-collapse
        v-if="!loading && filteredCourses.length > 0"
        v-model="activeNames"
        accordion
        class="custom-collapse">
      <el-collapse-item
          v-for="course in filteredCourses"
          :key="course.id"
          :name="String(course.id)">
        <template #title>
          <div class="course-header">
            <div class="course-title">
              <span :class="['font-bold', course.id === activeCourseId ? 'text-primary' : '']">
                《{{ course.name }}》
              </span>
              <el-tag
                  size="small"
                  class="ml-3"
                  :type="getAssignmentCountType(course.filteredAssignments.length)">
                {{ course.filteredAssignments.length }} 个作业
              </el-tag>
            </div>
            <div class="course-meta">
              <span class="update-time">
                <el-icon><Calendar/></el-icon>
                最近更新：{{ formatDate(course.update_time) }}
              </span>
            </div>
          </div>
        </template>

        <el-empty
            v-if="course.filteredAssignments.length === 0"
            description="没有符合筛选条件的作业"
            :image-size="100"/>

        <div class="assignment-grid">
          <el-card
              v-for="asg in course.filteredAssignments"
              :key="asg.id"
              shadow="hover"
              class="assignment-card"
              :body-style="{ padding: '20px' }">
            <div
                class="status-badge"
                :class="getAssignmentStatusClass(asg)">
              {{ getAssignmentStatusText(asg) }}
            </div>

            <div class="p-4">
              <div class="assignment-title">{{ asg.title }}</div>
              <div class="assignment-description">
                {{ truncateDescription(asg.description) }}
              </div>

              <div class="assignment-meta">
                <div class="meta-item">
                  <el-icon>
                    <Timer/>
                  </el-icon>
                  <span>截止：{{ formatDate(asg.due_date) }}</span>
                  <el-tag
                      v-if="!isOverdue(asg)"
                      size="small"
                      type="warning"
                      class="ml-1">
                    {{ getRemainingTime(asg.due_date) }}
                  </el-tag>
                </div>
                <div class="meta-item">
                  <el-icon>
                    <Trophy/>
                  </el-icon>
                  <span>满分：{{ asg.max_score }} 分</span>
                </div>
                <div class="meta-item">
                  <el-icon>
                    <User/>
                  </el-icon>
                  <span>发布：{{ asg.teacher_name }}</span>
                </div>
                <div class="meta-item">
                  <el-icon>
                    <Calendar/>
                  </el-icon>
                  <span>时间：{{ formatDate(asg.deploy_date) }}</span>
                </div>
              </div>

              <div class="assignment-actions">
                <el-tooltip
                    v-if="isOverdue(asg) && (!asg.submitted || asg.is_returned)"
                    content="该作业已截止，无法提交"
                    placement="top">
                  <el-button type="info" size="small" disabled>已截止</el-button>
                </el-tooltip>
                <el-tooltip
                    v-else-if="isOverdue(asg) && asg.submitted && !asg.is_returned"
                    content="该作业已截止"
                    placement="top">
                  <el-button type="primary" size="small" @click="goSubmit(asg.id)">查看提交</el-button>
                </el-tooltip>
                <template v-else>
                  <el-button type="primary" size="small" @click="goSubmit(asg.id)">
                    {{ isEffectivelySubmitted(asg) ? '查看/重新提交' : '去提交' }}
                  </el-button>
                </template>
                <el-button text size="small" @click="previewAssignment(asg)">查看详情</el-button>
              </div>
            </div>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-empty
        v-if="!loading && filteredCourses.length === 0 && courses.length > 0"
        description="没有符合筛选条件的作业"
        class="my-8">
      <el-button @click="statusFilter = 'all'">查看全部作业</el-button>
    </el-empty>

    <el-dialog v-model="previewDialogVisible" title="作业详情" width="600px" custom-class="assignment-dialog">
      <template v-if="currentAssignment">
        <div class="dialog-content">
          <h2 class="dialog-title">{{ currentAssignment.title }}</h2>
          <div class="dialog-info-row">
            <span class="info-label">所属课程:</span>
            <span class="info-value">{{ currentAssignment.course_class_name }}</span>
          </div>
          <div class="dialog-info-row">
            <span class="info-label">截止日期:</span>
            <span class="info-value" :class="{'text-red-500': isOverdue(currentAssignment)}">
              {{ formatDate(currentAssignment.due_date) }}
              <span v-if="!isOverdue(currentAssignment)" class="text-orange-500 ml-2">
                ({{ getRemainingTime(currentAssignment.due_date) }})
              </span>
            </span>
          </div>
          <div class="dialog-info-row">
            <span class="info-label">满分:</span>
            <span class="info-value">{{ currentAssignment.max_score }} 分</span>
          </div>
          <div class="dialog-info-row">
            <span class="info-label">发布:</span>
            <span class="info-value">{{ currentAssignment.teacher_name }}</span>
          </div>
          <div class="dialog-info-row">
            <span class="info-label">时间:</span>
            <span class="info-value">{{ formatDate(currentAssignment.deploy_date) }}</span>
          </div>
          <div class="dialog-info-row">
            <span class="info-label">状态:</span>
            <span class="info-value">
              <el-tag :type="getTagType(currentAssignment)">
                {{ getAssignmentStatusText(currentAssignment) }}
              </el-tag>
            </span>
          </div>

          <div class="dialog-info-row" v-if="getFinalScore(currentAssignment) !== null">
            <span class="info-label">得分</span>
            <span class="info-value">
              <el-tag :type="getScoreTagType(getFinalScore(currentAssignment))">
                {{ getFinalScore(currentAssignment) }} 分
              </el-tag>
            </span>
          </div>

          <div class="dialog-info-row" v-if="getFinalComment(currentAssignment)">
            <span class="info-label">评语:</span>
            <div class="info-value markdown-content" v-html="renderMarkdown(getFinalComment(currentAssignment))"></div>
          </div>

          <div class="dialog-info-row"
               v-if="currentAssignment.ai_grading_status === 'completed' && typeof currentAssignment.ai_generated_similarity === 'number'">
            <span class="info-label">AI疑似度:</span>
            <span class="info-value">
              <el-progress
                  :percentage="Math.round(currentAssignment.ai_generated_similarity * 100)"
                  :stroke-width="10"
                  :format="(percentage) => `${percentage}%`"
                  style="width: 150px;"/>
            </span>
          </div>
          <div class="dialog-info-row" v-if="currentAssignment.ai_grading_status === 'processing'">
            <span class="info-label">AI批改:</span>
            <span class="info-value"><el-tag type="info" effect="plain">正在处理中...</el-tag></span>
          </div>
          <div class="dialog-info-row" v-if="currentAssignment.ai_grading_status === 'failed'">
            <span class="info-label">AI批改:</span>
            <span class="info-value"><el-tag type="danger" effect="plain">处理失败</el-tag></span>
          </div>
          <div class="dialog-info-row" v-if="currentAssignment.ai_grading_status === 'skipped'">
            <span class="info-label">AI批改:</span>
            <span class="info-value"><el-tag type="warning" effect="plain">已跳过</el-tag></span>
          </div>


          <div class="mt-6">
            <div class="font-bold mb-2">作业描述:</div>
            <div class="description-box markdown-content" v-html="renderMarkdown(currentAssignment.description)"></div>
          </div>
        </div>
      </template>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="previewDialogVisible = false">关闭</el-button>
          <el-button
              type="primary"
              :disabled="isOverdue(currentAssignment) && (!currentAssignment.submitted || currentAssignment.is_returned)"
              @click="goSubmitFromPreview">
            {{
              (isOverdue(currentAssignment) && (!currentAssignment.submitted || currentAssignment.is_returned))
                  ? '已截止'
                  : (isEffectivelySubmitted(currentAssignment) ? '查看/修改提交' : '去提交')
            }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {computed, onMounted, ref, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import {Calendar, Timer, Trophy, User} from '@element-plus/icons-vue'
import {fetchCourseAssignments, fetchStudentCourses} from '@/api/student.js'
import MarkdownIt from 'markdown-it'; // 新增
import DOMPurify from 'dompurify'; // 新增
// 如果需要代码高亮 (可选)
// import hljs from 'highlight.js/lib/core';
// import python from 'highlight.js/lib/languages/python';
// import javascript from 'highlight.js/lib/languages/javascript';
// import 'highlight.js/styles/github.css'; // 或其他主题

// hljs.registerLanguage('python', python);
// hljs.registerLanguage('javascript', javascript);


// 配置 dayjs
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const error = ref(null)
const courses = ref([])
const statusFilter = ref('all') // 'all', 'pending', 'submitted', 'overdue'
const activeCourseId = ref(null)
const activeNames = ref([]) // For el-collapse active items
const previewDialogVisible = ref(false)
const currentAssignment = ref(null)

// 初始化 Markdown-it
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  // highlight: function (str, lang) { // 代码高亮 (可选)
  //   if (lang && hljs.getLanguage(lang)) {
  //     try {
  //       return '<pre class="hljs"><code>' +
  //              hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
  //              '</code></pre>';
  //     } catch (__) {}
  //   }
  //   return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
  // }
});

const renderMarkdown = (markdownText) => {
  if (!markdownText) return '';
  const rawHtml = md.render(markdownText);
  return DOMPurify.sanitize(rawHtml);
};


/**
 * 加载课程与作业
 */
const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const {data: courseList} = await fetchStudentCourses()
    const coursePromises = courseList.map(async (course) => {
      try {
        const {data: assignments} = await fetchCourseAssignments(course.id)
        const processedAssignments = (assignments || []).map(asg => ({
          ...asg,
          submitted: asg.submitted || false,
          is_returned: asg.is_returned || false,
          score: asg.score, // 可以为 null
          teacher_comment: asg.teacher_comment, // 可以为 null
          ai_score: asg.ai_score, // 可以为 null
          ai_comment: asg.ai_comment, // 可以为 null
          ai_generated_similarity: asg.ai_generated_similarity, // 可以为 null
          ai_grading_status: asg.ai_grading_status // 可以为 null 或 'pending', 'processing', etc.
        }));
        return {...course, assignments: processedAssignments, update_time: course.update_time || new Date(0)}; // 添加update_time默认值
      } catch (err) {
        console.error(`获取课程 ${course.name} (ID: ${course.id}) 的作业失败:`, err)
        return {...course, assignments: [], update_time: course.update_time || new Date(0)}
      }
    })
    courses.value = await Promise.all(coursePromises)
    sortCoursesAndAssignments()
    setActiveCourseFromRoute()
  } catch (err) {
    console.error('加载课程列表或其作业失败:', err)
    error.value = '加载数据失败，请刷新页面或联系管理员。'
  } finally {
    loading.value = false
  }
}

// 获取最终显示分数 (优先教师，其次AI)
const getFinalScore = (assignmentSubmission) => {
  if (assignmentSubmission.score !== null && typeof assignmentSubmission.score !== 'undefined') {
    return assignmentSubmission.score;
  }
  if (assignmentSubmission.ai_grading_status === 'completed' && assignmentSubmission.ai_score !== null && typeof assignmentSubmission.ai_score !== 'undefined') {
    return assignmentSubmission.ai_score;
  }
  return null; // 没有可显示的分数
};

// 获取最终显示评语
const getFinalComment = (assignmentSubmission) => {
  if (assignmentSubmission.teacher_comment) {
    return assignmentSubmission.teacher_comment;
  }
  if (assignmentSubmission.ai_grading_status === 'completed' && assignmentSubmission.ai_comment) {
    return assignmentSubmission.ai_comment;
  }
  return ''; // 没有可显示的评语
};


/**
 * 根据 update_time _time 倒序排序课程，作业按截止日期和状态排序
 */
const sortCoursesAndAssignments = () => {
  courses.value.sort((a, b) => dayjs(b.update_time).valueOf() - dayjs(a.update_time).valueOf());
  courses.value.forEach(course => {
    course.assignments.sort((a, b) => {
      const aOverdue = isOverdue(a);
      const bOverdue = isOverdue(b);
      if (aOverdue !== bOverdue) return aOverdue ? 1 : -1;

      const aEffectivelySubmitted = isEffectivelySubmitted(a);
      const bEffectivelySubmitted = isEffectivelySubmitted(b);
      if (aEffectivelySubmitted !== bEffectivelySubmitted) return aEffectivelySubmitted ? 1 : -1;

      return dayjs(a.due_date).valueOf() - dayjs(b.due_date).valueOf();
    });
  });
};


/**
 * 设置激活的课程（手风琴展开项）
 */
const setActiveCourseFromRoute = () => {
  const courseIdFromRoute = route.params.id ? String(route.params.id) : null;
  if (courseIdFromRoute && courses.value.some(c => String(c.id) === courseIdFromRoute)) {
    activeCourseId.value = courseIdFromRoute;
    activeNames.value = [courseIdFromRoute];
    return;
  }
  const firstCourseWithPending = courses.value.find(course =>
      course.assignments.some(asg => !isOverdue(asg) && (!asg.submitted || asg.is_returned))
  );
  if (firstCourseWithPending) {
    activeCourseId.value = String(firstCourseWithPending.id);
    activeNames.value = [String(firstCourseWithPending.id)];
    return;
  }
  if (courses.value.length > 0) {
    activeCourseId.value = String(courses.value[0].id);
    activeNames.value = [String(courses.value[0].id)];
  } else {
    activeCourseId.value = null;
    activeNames.value = [];
  }
}


/**
 * 跳转到作业提交页面
 */
const goSubmit = (assignmentId) => {
  router.push({name: 'StudentAssignmentSubmit', params: {id: assignmentId}})
}

/**
 * 从预览对话框跳转提交
 */
const goSubmitFromPreview = () => {
  if (currentAssignment.value) {
    if (isOverdue(currentAssignment.value) && (!currentAssignment.value.submitted || currentAssignment.value.is_returned)) {
      // 已截止且不能再提交
    } else {
      previewDialogVisible.value = false
      goSubmit(currentAssignment.value.id)
    }
  }
}

/**
 * 打开作业详情预览
 */
const previewAssignment = (assignment) => {
  currentAssignment.value = {...assignment}
  previewDialogVisible.value = true
}

/**
 * 判断作业是否已截止
 */
const isOverdue = (assignment) => {
  return assignment && assignment.due_date && dayjs(assignment.due_date).isBefore(dayjs())
}

/**
 * 判断作业是否已由学生有效提交（已提交且未被退回）
 */
const isEffectivelySubmitted = (assignment) => {
  return !!assignment.submitted && !assignment.is_returned;
};

/**
 * 获取作业状态文本
 */
const getAssignmentStatusText = (assignment) => {
  const finalScore = getFinalScore(assignment);

  if (isOverdue(assignment)) {
    if (assignment.is_returned) return '已截止 (曾退回)';
    if (assignment.submitted) {
      return (finalScore !== null) ? `已截止 (已评分 ${finalScore})` : '已截止 (已提交)';
    }
    return '已截止 (未提交)';
  }
  // Not overdue
  if (assignment.is_returned) return '已退回 (待重交)';
  if (assignment.submitted) {
    return (finalScore !== null) ? `已评分 (${finalScore})` : '已提交 (待批改)';
  }
  if (assignment.ai_grading_status === 'processing') return 'AI批改中...';
  return '待提交';
};


/**
 * 获取作业状态对应的CSS类名
 */
const getAssignmentStatusClass = (assignment) => {
  if (isOverdue(assignment)) return 'status-overdue';
  if (assignment.is_returned) return 'status-returned';
  if (assignment.submitted) {
    // 如果有AI正在处理，可以给一个特定状态
    if (assignment.ai_grading_status === 'processing') return 'status-processing';
    return 'status-submitted';
  }
  return 'status-pending';
};

/**
 * 获取标签类型 (for el-tag type prop)
 */
const getTagType = (assignment) => {
  const statusText = getAssignmentStatusText(assignment); // 使用更新后的状态文本
  if (statusText.includes('已截止')) return 'info';
  if (statusText.includes('已退回')) return 'warning';
  if (statusText.includes('已评分')) return 'success';
  if (statusText.includes('AI批改中')) return 'primary';
  if (statusText.includes('已提交')) return 'primary';
  return 'warning'; // 待提交
}

/**
 * 获取得分标签类型
 */
const getScoreTagType = (score) => {
  if (score === null || typeof score === 'undefined') return 'info';
  const numericScore = parseFloat(score);
  if (numericScore >= 80) return 'success';
  if (numericScore >= 60) return 'warning';
  return 'danger';
}

/**
 * 获取剩余时间文本
 */
const getRemainingTime = (dueDate) => {
  if (!dueDate) return '';
  const now = dayjs();
  const due = dayjs(dueDate);
  if (due.isBefore(now)) return '已截止';
  return '剩余 ' + due.fromNow(true);
}

/**
 * 格式化日期
 */
const formatDate = (dateString) => {
  if (!dateString) return '未知';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
}

/**
 * 截断描述文本
 */
const truncateDescription = (text) => {
  if (!text) return '暂无描述';
  return text.length > 50 ? text.substring(0, 50) + '...' : text;
}

/**
 * 基于数量获取标签类型
 */
const getAssignmentCountType = (count) => {
  if (count === 0) return 'info';
  if (count < 3) return 'success';
  if (count < 5) return 'warning';
  return 'danger';
}

// 计算属性
const filteredCourses = computed(() => {
  return courses.value.map(course => {
    const filteredAssignments = course.assignments.filter(asg => {
      const overdue = isOverdue(asg);
      // const effectivelySubmitted = isEffectivelySubmitted(asg); // 已定义
      const isPending = !overdue && (!asg.submitted || asg.is_returned) && asg.ai_grading_status !== 'processing';

      if (statusFilter.value === 'all') return true;
      if (statusFilter.value === 'pending') return isPending;
      if (statusFilter.value === 'submitted') return !overdue && isEffectivelySubmitted(asg) && asg.ai_grading_status !== 'processing';
      if (statusFilter.value === 'overdue') return overdue;
      return true;
    });
    return {...course, filteredAssignments};
  }).filter(course => course.filteredAssignments.length > 0 || statusFilter.value === 'all');
});


// 统计数据
const totalCourses = computed(() => courses.value.length);

const totalAssignments = computed(() => {
  return courses.value.reduce((total, course) => total + (course.assignments?.length || 0), 0);
});

const pendingAssignments = computed(() => {
  if (!courses.value || courses.value.length === 0) return 0;
  return courses.value.reduce((total, course) => {
    const courseAssignments = course.assignments || [];
    return total + courseAssignments.filter(asg => {
      return !isOverdue(asg) && (!asg.submitted || asg.is_returned) && asg.ai_grading_status !== 'processing';
    }).length;
  }, 0);
});

const overdueAssignments = computed(() => {
  if (!courses.value || courses.value.length === 0) return 0;
  return courses.value.reduce((total, course) => {
    const courseAssignments = course.assignments || [];
    return total + courseAssignments.filter(asg => isOverdue(asg)).length;
  }, 0);
});


// 生命周期钩子和监听器
onMounted(loadData)

watch(
    () => route.params.id,
    (newId) => {
      if (newId) {
        activeCourseId.value = String(newId);
        if (!activeNames.value.includes(String(newId))) {
          activeNames.value = [String(newId)];
        }
      } else {
        setActiveCourseFromRoute();
      }
    }
)
</script>

<style scoped>
.assignment-list-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-primary {
  color: var(--el-color-primary);
}

.loading-container {
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.courses-summary {
  margin-top: 20px;
}

.summary-card {
  text-align: center;
  padding: 16px;
  transition: transform 0.3s;
}

.summary-card:hover {
  transform: translateY(-5px);
}

.summary-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 14px;
  color: #666;
}

.bg-blue-50 {
  background-color: #e6f1f9;
}

.bg-green-50 {
  background-color: #e7f6e9;
}

.bg-orange-50 {
  background-color: #fef3e6;
}

.bg-red-50 {
  background-color: #fde9e9;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.course-meta {
  display: flex;
  align-items: center;
  color: #888;
  font-size: 13px;
}

.update-time {
  display: flex;
  align-items: center;
  gap: 4px;
}

.assignment-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.assignment-card {
  position: relative;
  overflow: hidden;
  transition: transform 0.2s;
  display: flex; /* 使用flex布局 */
  flex-direction: column; /* 垂直排列子元素 */
}

.assignment-card:hover {
  transform: translateY(-5px);
}

.assignment-card .el-card__body {
  display: flex;
  flex-direction: column;
  flex-grow: 1; /* 让内容区域填满卡片 */
}

.assignment-card .p-4 { /* 作业内容的主要容器 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* 将动作按钮推到底部 */
}


.status-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 4px 12px;
  color: white;
  font-size: 12px;
  font-weight: bold;
  border-bottom-left-radius: 8px;
}

.status-pending {
  background-color: #e6a23c; /* Element Plus Warning color */
}

.status-processing { /* 新增AI处理中状态 */
  background-color: var(--el-color-primary-light-3);
}

.status-submitted {
  background-color: #67c23a; /* Element Plus Success color */
}

.status-overdue {
  background-color: #f56c6c; /* Element Plus Danger color */
}

.status-returned {
  background-color: #909399; /* Element Plus Info color, or a custom warning color */
}


.assignment-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.assignment-description {
  color: #606266;
  font-size: 13px;
  margin-bottom: 12px;
  min-height: 38px;
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.assignment-meta {
  margin-bottom: 12px;
  border-top: 1px solid #eee;
  padding-top: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #666;
}

.assignment-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto; /* 将动作按钮推到底部 */
  padding-top: 10px; /* 给一点上边距 */
}

.assignment-dialog .dialog-content { /* 确保对话框内容区域有内边距 */
  padding: 0 20px 20px 20px;
}

.dialog-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.dialog-info-row {
  display: flex;
  align-items: flex-start; /* 顶部对齐，特别是评语可能较长 */
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.info-label {
  width: 80px;
  color: #606266;
  font-weight: 500;
  flex-shrink: 0;
  padding-right: 10px;
}

.info-value {
  flex-grow: 1;
  color: #303133;
}

.info-value .el-tag {
  font-size: 13px;
}


.description-box {
  background-color: #f9fafb;
  padding: 15px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14px;
  color: #303133;
  border: 1px solid #e4e7ed;
}

.custom-collapse :deep(.el-collapse-item__header) {
  background-color: #f5f7fa;
  padding: 10px 15px;
  border-radius: 4px;
  font-size: 15px;
}

.custom-collapse :deep(.el-collapse-item__wrap) {
  padding: 0; /* 移除内层padding，由assignment-grid控制 */
  background-color: #ffffff;
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  border: 1px solid #ebeef5;
  border-top: none;
}

.custom-collapse .el-collapse-item {
  margin-bottom: 10px;
  border-radius: 4px;
  overflow: hidden; /* 确保圆角生效 */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.custom-collapse .el-collapse-item:last-child {
  margin-bottom: 0;
}

.markdown-content {
  line-height: 1.7;
  color: #303133;
}

.markdown-content :deep(p) {
  margin-bottom: 0.8em;
}

.markdown-content :deep(ul), .markdown-content :deep(ol) {
  padding-left: 20px;
  margin-bottom: 0.8em;
}

.markdown-content :deep(code) {
  background-color: #f0f2f5;
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  border-radius: 3px;
}

.markdown-content :deep(pre code) {
  display: block;
  padding: 1em;
  overflow-x: auto;
  border-radius: 5px;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #d0d7de;
  padding-left: 1em;
  color: #57606a;
  margin-left: 0;
}
</style>