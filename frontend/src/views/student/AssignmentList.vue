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

              <div v-if="asg.ai_grading_status && asg.ai_grading_status !== 'pending'" class="ai-grading-info-list">
                <el-tag size="small" :type="getAiStatusTagType(asg.ai_grading_status)" effect="light">
                  AI批改: {{ getAiStatusText(asg.ai_grading_status) }}
                </el-tag>
                <el-tag v-if="asg.ai_grading_status === 'completed' && asg.ai_score !== null" size="small"
                        type="success" effect="light" class="ml-1">
                  AI评分: {{ asg.ai_score }}
                </el-tag>
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
                  <span>发布：{{ asg.deployer_name }}</span>
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
                  <el-button
                      type="info"
                      size="small"
                      disabled>
                    已截止
                  </el-button>
                </el-tooltip>
                <el-tooltip
                    v-else-if="isOverdue(asg) && asg.submitted && !asg.is_returned"
                    content="该作业已截止"
                    placement="top">
                  <el-button
                      type="primary"
                      size="small"
                      @click="goSubmit(asg.id)">
                    查看提交
                  </el-button>
                </el-tooltip>
                <template v-else>
                  <el-button
                      type="primary"
                      size="small"
                      @click="goSubmit(asg.id)">
                    {{ isEffectivelySubmitted(asg) ? '查看/修改提交' : '去提交' }}
                  </el-button>
                </template>

                <el-button
                    text
                    size="small"
                    @click="previewAssignment(asg)">
                  查看详情
                </el-button>
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

    <el-dialog
        v-model="previewDialogVisible"
        title="作业详情"
        width="700px"
        top="5vh"
        custom-class="assignment-preview-dialog"
    >
      <template v-if="currentAssignment">
        <div class="dialog-content">
          <h2 class="dialog-title">{{ currentAssignment.title }}</h2>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="所属课程">
              {{ currentAssignment.course_class_name }}
            </el-descriptions-item>
            <el-descriptions-item label="截止日期"
                                  :label-class-name="isOverdue(currentAssignment) ? 'text-red-500' : ''">
              <span :class="{'text-red-500 font-bold': isOverdue(currentAssignment)}">{{
                  formatDate(currentAssignment.due_date)
                }}</span>
              <el-tag v-if="!isOverdue(currentAssignment)" size="small" type="warning" class="ml-2">
                ({{ getRemainingTime(currentAssignment.due_date) }})
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="满分">{{ currentAssignment.max_score }} 分</el-descriptions-item>
            <el-descriptions-item label="发布教师">{{ currentAssignment.deployer_name }}</el-descriptions-item>
            <el-descriptions-item label="发布时间">{{
                formatDate(currentAssignment.deploy_date)
              }}
            </el-descriptions-item>
            <el-descriptions-item label="作业状态">
              <el-tag :type="getTagType(currentAssignment)">
                {{ getAssignmentStatusText(currentAssignment) }}
              </el-tag>
            </el-descriptions-item>

            <el-descriptions-item label="教师评分"
                                  v-if="currentAssignment.score !== null && typeof currentAssignment.score !== 'undefined' && !currentAssignment.is_returned">
              <el-tag :type="getScoreTagType(currentAssignment.score, currentAssignment.max_score)">
                {{ currentAssignment.score }} / {{ currentAssignment.max_score }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="教师评语"
                                  v-if="currentAssignment.teacher_comment && !currentAssignment.is_returned"
                                  :span="currentAssignment.score === null ? 2 : 1">
              <div class="comment-box">{{ currentAssignment.teacher_comment }}</div>
            </el-descriptions-item>
          </el-descriptions>

          <el-descriptions title="AI辅助批改" :column="1" border size="small" class="mt-4"
                           v-if="currentAssignment.ai_grading_status && currentAssignment.ai_grading_status !== 'pending'">
            <el-descriptions-item label="AI批改状态">
              <el-tag :type="getAiStatusTagType(currentAssignment.ai_grading_status)" effect="light">
                {{ getAiStatusText(currentAssignment.ai_grading_status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="AI评分"
                                  v-if="currentAssignment.ai_grading_status === 'completed' && currentAssignment.ai_score !== null">
              <el-tag type="success" effect="plain">{{ currentAssignment.ai_score }} /
                {{ currentAssignment.max_score }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="AI评语"
                                  v-if="currentAssignment.ai_grading_status === 'completed' && currentAssignment.ai_comment">
              <div class="comment-box markdown-content" v-html="renderMarkdown(currentAssignment.ai_comment)"></div>
            </el-descriptions-item>
            <el-descriptions-item label="AI生成疑似度"
                                  v-if="currentAssignment.ai_grading_status === 'completed' && currentAssignment.ai_generated_similarity !== null">
              <el-progress :percentage="Math.round(currentAssignment.ai_generated_similarity * 100)" :stroke-width="10"
                           :color="getSimilarityColor(currentAssignment.ai_generated_similarity)"/>
            </el-descriptions-item>
            <el-descriptions-item label="信息"
                                  v-if="currentAssignment.ai_grading_status === 'failed' || currentAssignment.ai_grading_status === 'skipped'">
              <div class="comment-box">{{ currentAssignment.ai_comment }}</div>
            </el-descriptions-item>
          </el-descriptions>

          <div class="mt-6">
            <div class="font-bold mb-2 text-gray-700">作业描述:</div>
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
              (isOverdue(currentAssignment) && (!currentAssignment.submitted || currentAssignment.is_returned)) ? '已截止' : (isEffectivelySubmitted(currentAssignment) ? '查看/修改提交' : '去提交')
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
import duration from 'dayjs/plugin/duration' // For more precise time differences
import 'dayjs/locale/zh-cn'
import {Calendar, Timer, Trophy, User} from '@element-plus/icons-vue'
import {fetchCourseAssignments, fetchStudentCourses} from '@/api/student.js'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
// import hljs from 'highlight.js' // For full markdown-it-highlightjs, usually just import the style
import 'highlight.js/styles/atom-one-dark.css'; // Choose a highlight.js theme

// 配置 dayjs
dayjs.extend(relativeTime)
dayjs.extend(duration)
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

// 创建并配置markdown-it实例
const md = new MarkdownIt({
  html: true,        // 启用HTML标签
  breaks: true,      // 将换行符转换为<br>
  linkify: true,     // 自动转换URL为链接
  typographer: true, // 启用一些语言中立的替换和引号
  highlight: function (str, lang) { // 使用 highlight.js 进行代码高亮
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
            hljs.highlight(str, {language: lang, ignoreIllegals: true}).value +
            '</code></pre>';
      } catch (__) {
      }
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
  }
});

const renderMarkdown = (markdownText) => {
  if (!markdownText) return '';
  const renderedHTML = md.render(markdownText);
  return DOMPurify.sanitize(renderedHTML);
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
        const {data: assignments} = await fetchCourseAssignments(course.id) // API应返回包含AI字段的数据
        const processedAssignments = (assignments || []).map(asg => ({
          ...asg,
          submitted: asg.submitted || false,
          is_returned: asg.is_returned || false,
          score: asg.score, // Can be null
          // 确保AI相关字段有默认值，如果API没返回
          ai_score: asg.ai_score !== undefined ? asg.ai_score : null,
          ai_comment: asg.ai_comment || null,
          ai_grading_status: asg.ai_grading_status || 'pending', // 'pending' 'processing' 'completed' 'failed' 'skipped'
          ai_generated_similarity: asg.ai_generated_similarity !== undefined ? asg.ai_generated_similarity : null,
        }));
        return {...course, assignments: processedAssignments};
      } catch (err) {
        console.error(`获取课程 ${course.name} (ID: ${course.id}) 的作业失败:`, err)
        return {...course, assignments: []}
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

// ... (sortCoursesAndAssignments, setActiveCourseFromRoute, goSubmit, goSubmitFromPreview, previewAssignment, isOverdue, isEffectivelySubmitted 保持不变) ...
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

const goSubmit = (assignmentId) => {
  router.push({name: 'StudentAssignmentSubmit', params: {id: assignmentId}})
}

const goSubmitFromPreview = () => {
  if (currentAssignment.value) {
    if (isOverdue(currentAssignment.value) && (!currentAssignment.value.submitted || currentAssignment.value.is_returned)) {
      // Already disabled
    } else {
      previewDialogVisible.value = false
      goSubmit(currentAssignment.value.id)
    }
  }
}

const previewAssignment = (assignment) => {
  currentAssignment.value = {...assignment}
  previewDialogVisible.value = true
}

const isOverdue = (assignment) => {
  return assignment && assignment.due_date && dayjs(assignment.due_date).isBefore(dayjs())
}

const isEffectivelySubmitted = (assignment) => {
  return !!assignment.submitted && !assignment.is_returned;
};


/**
 * 获取作业状态文本 (更新以包含AI信息)
 */
const getAssignmentStatusText = (assignment) => {
  let statusText = '';
  const teacherGraded = assignment.score !== null && typeof assignment.score !== 'undefined' && !assignment.is_returned;

  if (isOverdue(assignment)) {
    statusText = '已截止';
    if (assignment.is_returned) statusText += ' (曾退回)';
    else if (teacherGraded) statusText += ` (师评 ${assignment.score})`;
    else if (assignment.submitted) statusText += ' (已提交)';
    else statusText += ' (未提交)';
  } else { // 未截止
    if (assignment.is_returned) statusText = '已退回 (待重交)';
    else if (teacherGraded) statusText = `已师评 (${assignment.score})`;
    else if (assignment.submitted) statusText = '已提交 (待批改)';
    else statusText = '待提交';
  }

  // AI 状态补充 (如果AI已完成且教师未评分)
  if (assignment.ai_grading_status === 'completed' && !teacherGraded && assignment.ai_score !== null) {
    statusText += ` (AI预评 ${assignment.ai_score})`;
  } else if (assignment.ai_grading_status === 'processing' && !teacherGraded) {
    statusText += ' (AI批改中)';
  }

  return statusText;
};

const getAiStatusText = (status) => {
  const map = {
    pending: '待处理',
    processing: '处理中...',
    completed: '已完成',
    failed: '批改失败',
    skipped: '已跳过(不适用AI)',
  };
  return map[status] || '未知状态';
};

const getAiStatusTagType = (status) => {
  const map = {
    pending: 'info',
    processing: 'primary',
    completed: 'success',
    failed: 'danger',
    skipped: 'warning',
  };
  return map[status] || 'info';
};


/**
 * 获取作业状态对应的CSS类名
 */
const getAssignmentStatusClass = (assignment) => {
  if (isOverdue(assignment)) return 'status-overdue';
  if (assignment.is_returned) return 'status-returned';
  if (assignment.score !== null && typeof assignment.score !== 'undefined') return 'status-graded'; // 教师已评分
  if (assignment.submitted) return 'status-submitted';
  return 'status-pending';
};

/**
 * 获取标签类型 (for el-tag type prop)
 */
const getTagType = (assignment) => {
  // 优先显示教师评分状态
  if (assignment.score !== null && typeof assignment.score !== 'undefined' && !assignment.is_returned) return 'success'; // 师评
  if (assignment.is_returned) return 'warning'; // 退回
  if (assignment.submitted && assignment.ai_grading_status === 'completed' && assignment.ai_score !== null) return 'primary'; // AI已评
  if (assignment.submitted) return 'primary'; // 已提交，待批
  if (isOverdue(assignment)) return 'info'; // 已截止未提交
  return 'warning'; // 待提交
}

/**
 * 获取得分标签类型
 */
const getScoreTagType = (score, maxScore = 100) => {
  if (score === null || typeof score === 'undefined') return 'info';
  const percentage = (parseFloat(score) / parseFloat(maxScore)) * 100;
  if (percentage >= 85) return 'success';
  if (percentage >= 60) return 'warning';
  return 'danger';
}

const getSimilarityColor = (similarity) => {
  if (similarity === null || typeof similarity === 'undefined') return '#909399'; // info
  if (similarity >= 0.7) return '#F56C6C'; // danger
  if (similarity >= 0.4) return '#E6A23C'; // warning
  return '#67C23A'; // success
};


/**
 * 获取剩余时间文本
 */
const getRemainingTime = (dueDate) => {
  if (!dueDate) return '';
  const now = dayjs();
  const due = dayjs(dueDate);
  if (due.isBefore(now)) return '已截止';

  const durationObj = dayjs.duration(due.diff(now));
  const days = Math.floor(durationObj.asDays());
  const hours = durationObj.hours();
  const minutes = durationObj.minutes();

  if (days > 0) return `剩 ${days}天 ${hours}小时`;
  if (hours > 0) return `剩 ${hours}小时 ${minutes}分钟`;
  if (minutes > 0) return `剩 ${minutes}分钟`;
  return '即将截止';
}

// ... (formatDate, truncateDescription, getAssignmentCountType, filteredCourses, 统计数据, onMounted, watch 保持不变) ...
const formatDate = (dateString) => {
  if (!dateString) return '未知';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
}

const truncateDescription = (text) => {
  if (!text) return '暂无描述';
  return text.length > 50 ? text.substring(0, 50) + '...' : text;
}

const getAssignmentCountType = (count) => {
  if (count === 0) return 'info';
  if (count < 3) return 'success';
  if (count < 5) return 'warning';
  return 'danger';
}

const filteredCourses = computed(() => {
  return courses.value.map(course => {
    const filteredAssignments = course.assignments.filter(asg => {
      const overdue = isOverdue(asg);
      const effectivelySubmitted = isEffectivelySubmitted(asg);
      const isPending = !overdue && (!asg.submitted || asg.is_returned);

      if (statusFilter.value === 'all') return true;
      if (statusFilter.value === 'pending') return isPending;
      if (statusFilter.value === 'submitted') return !overdue && effectivelySubmitted; // 已提交指学生已交且未被退回，未截止
      if (statusFilter.value === 'overdue') return overdue;
      return true;
    });
    return {...course, filteredAssignments};
  }).filter(course => course.filteredAssignments.length > 0 || statusFilter.value === 'all');
});


const totalCourses = computed(() => courses.value.length);

const totalAssignments = computed(() => {
  return courses.value.reduce((total, course) => total + (course.assignments?.length || 0), 0);
});

const pendingAssignments = computed(() => {
  if (!courses.value || courses.value.length === 0) return 0;
  return courses.value.reduce((total, course) => {
    const courseAssignments = course.assignments || [];
    return total + courseAssignments.filter(asg => {
      return !isOverdue(asg) && (!asg.submitted || asg.is_returned);
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
  font-size: 28px; /* Adjusted size */
  font-weight: bold;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 13px; /* Adjusted size */
  color: #666;
}

.bg-blue-50 {
  background-color: #ecf5ff;
  color: #409EFF;
}

.bg-green-50 {
  background-color: #f0f9eb;
  color: #67C23A;
}

.bg-orange-50 {
  background-color: #fdf6ec;
  color: #E6A23C;
}

.bg-red-50 {
  background-color: #fef0f0;
  color: #F56C6C;
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
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); /* Increased minmax */
  gap: 20px; /* Increased gap */
  margin-top: 16px;
}

.assignment-card {
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 8px; /* Added border-radius */
}

.assignment-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); /* Enhanced shadow */
}

.status-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 5px 12px; /* Adjusted padding */
  color: white;
  font-size: 12px;
  font-weight: bold;
  border-bottom-left-radius: 8px;
  border-top-right-radius: 8px; /* Match card radius */
}

.status-pending {
  background-color: #E6A23C;
}

.status-submitted {
  background-color: #409EFF;
}

/* Changed to primary */
.status-graded {
  background-color: #67C23A;
}

.status-overdue {
  background-color: #F56C6C;
}

.status-returned {
  background-color: #909399;
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

.ai-grading-info-list {
  margin-bottom: 10px;
  font-size: 12px;
}

.assignment-meta {
  margin-bottom: 12px;
  border-top: 1px solid #f0f0f0; /* Lighter border */
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
  margin-top: 16px;
}

.dialog-content {
  padding: 0px 10px 10px 10px; /* Less padding on top */
}

.dialog-title {
  font-size: 20px; /* Slightly larger */
  font-weight: bold;
  margin-bottom: 20px; /* More space */
  padding-bottom: 10px; /* More space */
  border-bottom: 1px solid #eee;
  text-align: center; /* Center title */
}

.comment-box {
  background-color: #f9fafb; /* Slightly different background */
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 14px;
  border: 1px solid #e5e7eb; /* Light border */
  max-height: 150px;
  overflow-y: auto;
}

.markdown-content :deep(pre) {
  background-color: #2d2d2d; /* Dark background for code blocks */
  color: #f8f8f2; /* Light text for code blocks */
  padding: 1em;
  overflow: auto;
  border-radius: 5px;
  margin: 1em 0;
  font-family: 'Courier New', Courier, monospace;
}

.markdown-content :deep(code:not(.hljs)) { /* Inline code */
  background-color: #eef1f5;
  color: #c0341d;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}


.custom-collapse :deep(.el-collapse-item__header) {
  background-color: #fcfcfc; /* Lighter header */
  padding: 12px 20px; /* Adjusted padding */
  border-radius: 6px; /* Slightly more radius */
  border: 1px solid #ebeef5;
  font-size: 15px; /* Slightly larger font */
}

.custom-collapse :deep(.el-collapse-item__header.is-active) {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom: none;
}

.custom-collapse :deep(.el-collapse-item__wrap) {
  padding: 20px;
  background-color: #ffffff;
  border: 1px solid #ebeef5;
  border-top: none;
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

.custom-collapse .el-collapse-item {
  margin-bottom: 12px; /* More space */
}

.custom-collapse .el-collapse-item:last-child {
  margin-bottom: 0;
}

.assignment-preview-dialog .el-dialog__body {
  padding-top: 10px; /* Reduce top padding for dialog body */
}
</style>