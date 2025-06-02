<template>
  <div class="p-6 space-y-6">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="提交 / 编辑" name="edit">
        <div class="assignment-container p-6">
          <el-skeleton v-if="loading" animated :rows="6"/>
          <el-alert
              v-else-if="loadError"
              type="error"
              :closable="false"
              :title="loadError"
              show-icon
          />
          <template v-else>
            <div class="mb-6 flex items-center justify-between">
              <el-button
                  @click="$router.push('/student/assignments')"
                  plain
              >
                <el-icon class="mr-1">
                  <ArrowLeft/>
                </el-icon>
                返回作业列表
              </el-button>
              <el-tag
                  size="large"
                  :type="isOverdue ? 'danger' : 'success'">
                {{ isOverdue ? '已截止' : '进行中' }}
              </el-tag>
            </div>

            <el-card class="mb-6" shadow="hover">
              <div class="assignment-header">
                <h1 class="text-2xl font-bold mb-2">{{ assignment.title }}</h1>
                <div class="text-gray-500 mb-4 text-sm">《{{ assignment.course_class_name }}》</div>
              </div>
              <el-divider/>
              <div class="info-cards">
                <el-card class="info-card" shadow="hover">
                  <div class="info-card-content">
                    <el-icon class="info-icon">
                      <Clock/>
                    </el-icon>
                    <div class="info-title">截止</div>
                    <div :class="{'text-danger font-semibold': isOverdue}" class="info-value">
                      {{ formatDateTime(assignment.due_date) }}
                    </div>
                    <el-tag v-if="!isOverdue" size="small" type="warning" class="mt-2">
                      剩余 {{ remainingTime }}
                    </el-tag>
                  </div>
                </el-card>
                <el-card class="info-card" shadow="hover">
                  <div class="info-card-content">
                    <el-icon class="info-icon">
                      <Trophy/>
                    </el-icon>
                    <div class="info-title">满分</div>
                    <div class="info-value">{{ assignment.max_score }} 分</div>
                  </div>
                </el-card>
                <el-card class="info-card" shadow="hover">
                  <div class="info-card-content">
                    <el-icon class="info-icon">
                      <Calendar/>
                    </el-icon>
                    <div class="info-title">发布时间</div>
                    <div class="info-value">{{ formatDateTime(assignment.deploy_date) }}</div>
                  </div>
                </el-card>
                <el-card class="info-card" shadow="hover">
                  <div class="info-card-content">
                    <el-icon class="info-icon">
                      <User/>
                    </el-icon>
                    <div class="info-title">发布教师</div>
                    <div class="info-value">{{ assignment.deployer_name }}</div>
                  </div>
                </el-card>
              </div>
              <div class="mt-6">
                <div class="font-medium text-lg mb-2 flex items-center">
                  <el-icon class="mr-2">
                    <Document/>
                  </el-icon>
                  作业要求
                </div>
                <div class="description-box p-4 bg-gray-50 rounded-md markdown-content"
                     v-html="formattedDescription"></div>
              </div>
            </el-card>

            <template
                v-if="isEffectivelySubmitted(mySubmissionDetails) || (mySubmissionDetails && mySubmissionDetails.is_returned)">
              <el-card class="mb-6" shadow="hover">
                <template #header>
                  <div class="flex items-center justify-between">
                    <div class="flex items-center">
                      <el-icon :color="headerIconColor" class="mr-2">
                        <component :is="headerIcon"/>
                      </el-icon>
                      <span class="font-bold">{{ submissionStatusTitle }}</span>
                    </div>
                    <el-button
                        v-if="!isOverdue && !teacherHasGraded"
                        type="warning"
                        plain
                        size="small"
                        @click="prepareReSubmit">
                      修改提交
                    </el-button>
                  </div>
                </template>

                <div class="submission-info p-4 space-y-3">
                  <p><span class="font-medium text-gray-600">我的提交时间:</span>
                    {{ formatDateTime(mySubmissionDetails?.submit_time) }}</p>

                  <div v-if="teacherHasGraded">
                    <p><span class="font-medium text-gray-600">教师评分:</span>
                      <el-tag :type="getScoreTagType(mySubmissionDetails.score, assignment.max_score)" effect="light"
                              size="large" class="ml-2">
                        {{ mySubmissionDetails.score }} / {{ assignment.max_score }}
                      </el-tag>
                    </p>
                    <div v-if="mySubmissionDetails.teacher_comment" class="mt-2">
                      <p class="font-medium text-gray-600 mb-1">教师评语:</p>
                      <div class="comment-display-box markdown-content"
                           v-html="renderMarkdown(mySubmissionDetails.teacher_comment)"></div>
                    </div>
                  </div>
                  <div v-else-if="mySubmissionDetails && mySubmissionDetails.is_returned">
                    <el-alert title="作业被退回" type="warning" show-icon :closable="false">
                      <p v-if="mySubmissionDetails.teacher_comment">教师说明: {{
                          mySubmissionDetails.teacher_comment
                        }}</p>
                      <p v-else>教师已将您的作业退回，请修改后重新提交。</p>
                    </el-alert>
                  </div>

                  <div
                      v-if="mySubmissionDetails?.ai_grading_status && mySubmissionDetails.ai_grading_status !== 'pending'"
                      class="mt-4 pt-3 border-t border-gray-200">
                    <p class="font-medium text-gray-600 mb-2 text-sm flex items-center">
                      <el-icon class="mr-1">
                        <MagicStick/>
                      </el-icon>
                      AI辅助分析
                      <el-tag :type="getAiStatusTagType(mySubmissionDetails.ai_grading_status)" size="small"
                              class="ml-2">{{ getAiStatusText(mySubmissionDetails.ai_grading_status) }}
                      </el-tag>
                    </p>
                    <template v-if="mySubmissionDetails.ai_grading_status === 'completed'">
                      <p v-if="mySubmissionDetails.ai_score !== null">
                        <span class="font-medium text-gray-500 text-xs">AI建议分数:</span>
                        <el-tag type="info" effect="plain" size="small" class="ml-2">
                          {{ mySubmissionDetails.ai_score }} / {{ assignment.max_score }}
                        </el-tag>
                      </p>
                      <div v-if="mySubmissionDetails.ai_comment" class="mt-2">
                        <p class="font-medium text-gray-500 text-xs mb-1">AI评语参考:</p>
                        <div class="comment-display-box markdown-content bg-blue-50 text-sm"
                             v-html="renderMarkdown(mySubmissionDetails.ai_comment)"></div>
                      </div>
                      <div v-if="mySubmissionDetails.ai_generated_similarity !== null" class="mt-2">
                        <p class="font-medium text-gray-500 text-xs mb-1">AI生成内容疑似度:</p>
                        <el-progress :percentage="Math.round(mySubmissionDetails.ai_generated_similarity * 100)"
                                     :stroke-width="8"
                                     :color="getSimilarityColor(mySubmissionDetails.ai_generated_similarity)"/>
                      </div>
                    </template>
                    <div
                        v-else-if="mySubmissionDetails.ai_grading_status === 'failed' || mySubmissionDetails.ai_grading_status === 'skipped'"
                        class="mt-2">
                      <el-alert :title="getAiStatusText(mySubmissionDetails.ai_grading_status)" type="info" show-icon
                                :description="mySubmissionDetails.ai_comment || 'AI未能完成批改。'" :closable="false"/>
                    </div>
                  </div>

                  <div class="files-list mt-4" v-if="mySubmissionDetails?.files?.length">
                    <p class="font-medium text-gray-600 mb-2">我的提交文件:</p>
                    <div
                        v-for="file in mySubmissionDetails.files"
                        :key="file.id || file.name"
                        class="file-item">
                      <el-icon>
                        <Document/>
                      </el-icon>
                      <span class="file-name-text">{{ file.name || file.original_name }}</span>
                    </div>
                  </div>
                </div>
              </el-card>
            </template>

            <el-card v-if="showSubmitForm" shadow="hover">
              <template #header>
                <div class="font-bold flex items-center">
                  <el-icon class="mr-2">
                    <UploadFilled/>
                  </el-icon>
                  {{
                    mySubmissionDetails && mySubmissionDetails.id && !mySubmissionDetails.is_returned ? '修改提交内容' : '提交我的作业'
                  }}
                </div>
              </template>
              <el-form ref="formRef" :model="form" label-position="top">
                <el-form-item label="作业附件" required>
                  <el-upload
                      v-model:file-list="form.files"
                      :action="submitUrl"
                      :http-request="customHttpRequest"
                      :auto-upload="false"
                      :limit="3"
                      drag
                      multiple
                      :on-exceed="handleExceed"
                      :on-change="handleFileSelectChange"
                      :before-upload="handleBeforeUpload"
                      class="w-full"
                  >
                    <el-icon class="el-icon--upload">
                      <UploadFilled/>
                    </el-icon>
                    <div class="el-upload__text">
                      将文件拖到此处，或 <em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip text-gray-500">
                        * 最多可上传3个文件，每个文件不超过10MB，总大小不超过50MB。
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
                <el-form-item label="备注说明 (可选)">
                  <div class="quill-editor-wrapper">
                    <QuillEditor
                        v-model:content="form.comment"
                        contentType="html"
                        theme="snow"
                        :toolbar="editorToolbarOptions"
                        placeholder="可以在这里添加对作业的补充说明..."
                        style="height: 150px;"
                    />
                  </div>
                </el-form-item>
                <el-form-item class="mt-6 text-center">
                  <el-button
                      type="primary"
                      @click="handleSubmit"
                      :loading="submitting"
                      :disabled="isOverdue || form.files.length === 0"
                      size="large"
                  >
                    {{
                      isOverdue ? '已截止' : (mySubmissionDetails && mySubmissionDetails.id && !mySubmissionDetails.is_returned ? '确认修改' : '确认提交')
                    }}
                  </el-button>
                  <el-button @click="$router.push('/student/assignments')" size="large">取消</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </template>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史提交记录" name="history" lazy>
        <submission-history-tab
            v-if="activeTab === 'history'"
            :submissions="assignment.submissions || []"
            @load-submission-to-form="loadHistoryToForm"
            @delete-submission="handleDeleteSubmission"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import {ref, onMounted, computed, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import duration from 'dayjs/plugin/duration'
import 'dayjs/locale/zh-cn'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Trophy,
  User,
  Document,
  UploadFilled,
  CircleCheckFilled,
  WarningFilled,
  MagicStick,
  InfoFilled
} from '@element-plus/icons-vue' // Added icons
import {fetchAssignmentInfo, submitAssignmentWithFiles, updateSubmission, deleteDrawSubmission} from '@/api/student.js' // updateSubmission API
import {QuillEditor} from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
// import hljs from 'highlight.js'; // For markdown-it-highlightjs
import 'highlight.js/styles/atom-one-dark.css'; // Or your preferred theme
import SubmissionHistoryTab from '@/views/student/SubmissionHistoryTab.vue' // Ensure this component exists and is correctly imported

dayjs.extend(relativeTime)
dayjs.extend(duration)
dayjs.locale('zh-cn')

const props = defineProps({id: {type: [String, Number], required: true}}) // assignmentId
const router = useRouter()
const route = useRoute()

const activeTab = ref('edit')
const loading = ref(true)
const loadError = ref('')
const assignment = ref({}) // 作业本身的信息
const mySubmissionDetails = ref(null) // 学生对该作业的最新一次有效提交详情（或被退回的）

const formRef = ref()
const form = ref({
  files: [], // 用于el-upload的fileList
  comment: '',
  // title: '' // 学生通常不修改作业标题，而是提交内容
})
const submitting = ref(false)

// Markdown-it instance
const md = new MarkdownIt({
  html: true, breaks: true, linkify: true, typographer: true,
  highlight: function (str, lang) {
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
})

const renderMarkdown = (markdownText) => {
  if (!markdownText) return '';
  const renderedHTML = md.render(markdownText);
  return DOMPurify.sanitize(renderedHTML);
};

const editorToolbarOptions = [
  ['bold', 'italic', 'underline'],
  [{'list': 'ordered'}, {'list': 'bullet'}],
  ['link', 'code-block']
];

const isOverdue = computed(() => {
  if (!assignment.value?.due_date) return false;
  return dayjs(assignment.value.due_date).isBefore(dayjs());
});

// 学生是否已提交且未被退回
const isEffectivelySubmitted = (submission) => {
  return submission && submission.id && submission.submitted && !submission.is_returned;
};

// 教师是否已评分
const teacherHasGraded = computed(() => {
  return mySubmissionDetails.value &&
      mySubmissionDetails.value.score !== null &&
      typeof mySubmissionDetails.value.score !== 'undefined' &&
      !mySubmissionDetails.value.is_returned;
});


// 控制提交表单的显示：
// 1. 作业未截止，且 (学生从未提交过 OR 学生提交过但被退回了)
// 2. 或者，教师允许在评分前修改 (当前逻辑是评分前可以修改，通过prepareReSubmit触发)
const showSubmitForm = computed(() => {
  if (isOverdue.value && !(mySubmissionDetails.value && mySubmissionDetails.value.id && !teacherHasGraded.value)) return false; // 如果已截止，只有在“修改”状态才能显示
  if (teacherHasGraded.value) return false; // 教师已评分，不能再提交/修改
  return !isEffectivelySubmitted(mySubmissionDetails.value) || isPreparingReSubmit.value;
});
const isPreparingReSubmit = ref(false); // 用于标记用户点击了“修改提交”

const prepareReSubmit = () => {
  isPreparingReSubmit.value = true;
  // 将当前提交内容填充到表单（如果需要）
  if (mySubmissionDetails.value) {
    form.value.comment = mySubmissionDetails.value.content || '';
    // 文件需要用户重新选择，但可以提示已上传的文件
    form.value.files = []; // 清空待上传列表
    if (mySubmissionDetails.value.files && mySubmissionDetails.value.files.length > 0) {
      ElMessage.info(`您之前已上传 ${mySubmissionDetails.value.files.length} 个文件，若需保留请重新选择，否则将被新文件覆盖。`);
    }
  }
};


const submissionStatusTitle = computed(() => {
  if (teacherHasGraded.value) return "教师已批改";
  if (mySubmissionDetails.value?.is_returned) return "作业已退回";
  if (isEffectivelySubmitted(mySubmissionDetails.value)) return "我的提交详情";
  return "提交状态";
});

const headerIcon = computed(() => {
  if (teacherHasGraded.value) return CircleCheckFilled;
  if (mySubmissionDetails.value?.is_returned) return WarningFilled;
  if (isEffectivelySubmitted(mySubmissionDetails.value)) return InfoFilled;
  return UploadFilled;
});

const headerIconColor = computed(() => {
  if (teacherHasGraded.value) return '#67C23A'; // success
  if (mySubmissionDetails.value?.is_returned) return '#E6A23C'; // warning
  if (isEffectivelySubmitted(mySubmissionDetails.value)) return '#409EFF'; // primary
  return '#909399'; // info
});


const formattedDescription = computed(() => {
  if (!assignment.value?.description) return '<p class="text-gray-500">暂无作业描述。</p>';
  return renderMarkdown(assignment.value.description);
});

const remainingTime = computed(() => {
  if (!assignment.value?.due_date) return '';
  const now = dayjs();
  const due = dayjs(assignment.value.due_date);
  if (due.isBefore(now)) return '已截止';

  const durationObj = dayjs.duration(due.diff(now));
  const days = Math.floor(durationObj.asDays());
  const hours = durationObj.hours();
  const minutes = durationObj.minutes();

  if (days > 0) return `${days}天 ${hours}小时`;
  if (hours > 0) return `${hours}小时 ${minutes}分钟`;
  if (minutes > 0) return `${minutes}分钟`;
  return '即将截止';
});

const getScoreTagType = (score, maxScore = 100) => {
  if (score === null || typeof score === 'undefined') return 'info';
  const percentage = (parseFloat(score) / parseFloat(maxScore)) * 100;
  if (percentage >= 85) return 'success';
  if (percentage >= 70) return 'primary';
  if (percentage >= 60) return 'warning';
  return 'danger';
};

const getAiStatusText = (status) => {
  const map = {
    pending: '待处理', processing: 'AI处理中...', completed: 'AI分析完成',
    failed: 'AI分析失败', skipped: '不适用AI分析',
  };
  return map[status] || '未知AI状态';
};

const getAiStatusTagType = (status) => {
  const map = {
    pending: 'info', processing: 'primary', completed: 'success',
    failed: 'danger', skipped: 'warning',
  };
  return map[status] || 'info';
};

const getSimilarityColor = (similarity) => {
  if (similarity === null || typeof similarity === 'undefined') return '#909399';
  if (similarity >= 0.7) return '#F56C6C';
  if (similarity >= 0.4) return '#E6A23C';
  return '#67C23A';
};


const formatDateTime = (dateString) => {
  if (!dateString) return '未知';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
};

const handleFileSelectChange = (file, fileList) => {
  // fileList已经是el-upload内部维护的，这里主要用于触发校验或自定义逻辑
  form.value.files = fileList; // 确保我们的form.files与el-upload同步
};

const handleBeforeUpload = (rawFile) => {
  const allowedTypes = ['text/plain', 'text/x-python', 'text/html', 'application/javascript', 'application/x-sh', 'application/json', 'text/markdown', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/pdf', 'image/jpeg', 'image/png', 'application/zip', 'application/x-rar-compressed'];
  const maxSize = 10 * 1024 * 1024; // 10MB per file

  // if (!allowedTypes.includes(rawFile.type)) { // 文件类型检查可以更宽松，后端会有严格校验
  //   ElMessage.error(`文件类型不支持: ${rawFile.name}`);
  //   return false;
  // }
  if (rawFile.size > maxSize) {
    ElMessage.error(`文件 ${rawFile.name} 大小超过10MB限制!`);
    return false;
  }
  return true;
};

const handleExceed = (files) => {
  ElMessage.warning(`当前限制选择 3 个文件，本次选择了 ${files.length} 个文件，共选择了 ${files.length + form.value.files.length} 个文件`);
};

// 自定义上传方法，覆盖el-upload的默认行为，因为我们是手动构建FormData
const customHttpRequest = ({file, onSuccess, onError, onProgress}) => {
  // 我们不在这里单独上传，而是在handleSubmit中统一处理
  // 这个方法必须存在以阻止el-upload的默认上传行为
  // 可以简单地调用onSuccess()来表示文件已“处理”（加入列表）
  onSuccess();
};


const handleSubmit = async () => {
  if (!formRef.value) return;

  if (form.value.files.length === 0) {
    ElMessage.warning('请至少选择一个文件进行提交。');
    return;
  }

  let totalSize = 0;
  for (const file of form.value.files) {
    if (!file.raw) { // el-upload的fileList中，新选的文件有raw属性
      ElMessage.error('文件列表中包含无效文件，请重新选择。');
      return;
    }
    totalSize += file.raw.size;
  }
  if (totalSize > 50 * 1024 * 1024) { // 50MB total
    ElMessage.error('上传文件总大小不能超过50MB。');
    return;
  }

  if (isOverdue.value && !isPreparingReSubmit.value && !(mySubmissionDetails.value && mySubmissionDetails.value.is_returned)) {
    ElMessage.error('该作业已截止，无法提交。');
    return;
  }

  try {
    await ElMessageBox.confirm(
        `确定要${mySubmissionDetails.value?.id && !mySubmissionDetails.value?.is_returned ? '修改并覆盖原提交' : '提交新作业'}吗？`,
        '提交确认',
        {confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'}
    );
  } catch {
    return; // User cancelled
  }

  const fd = new FormData();
  fd.append("assignment", props.id); // assignment ID
  fd.append('title', assignment.value.title); // Use original assignment title or let user set one
  fd.append('content', form.value.comment || ''); // Student's comment/text content
  form.value.files.forEach(f => {
    if (f.raw) fd.append('files', f.raw, f.name); // Make sure to append raw file
  });

  submitting.value = true;
  try {
    let response;
    if (mySubmissionDetails.value?.id && isPreparingReSubmit.value) { // 如果是修改提交 (之前点击了“修改提交”按钮)
      // 后端需要支持PATCH方法来更新提交，或允许重新POST（并处理旧提交）
      // 假设后端 `submitAssignmentWithFiles` 或类似接口能处理覆盖逻辑
      // 或者，我们先删除旧的，再创建新的（如果业务逻辑如此）
      // 这里我们用 updateSubmission，它需要 submission ID
      // 确保 updateSubmission API 能处理 FormData
      // response = await updateSubmission(mySubmissionDetails.value.id, fd); // 假设 updateSubmission 接受 FormData
      // 鉴于后端AI逻辑在create时触发，我们通常建议学生“撤回再提交”或后端支持POST覆盖
      // 如果是简单的覆盖，可以直接调用创建接口，后端判断并处理
      ElMessage.info("正在尝试覆盖提交..."); // 提示用户
      response = await submitAssignmentWithFiles(props.id, fd); // 重新提交（后端处理覆盖）
    } else { // 新提交
      response = await submitAssignmentWithFiles(props.id, fd);
    }
    ElMessage.success('作业提交成功！');
    // 刷新数据
    await loadInitialData();
    activeTab.value = 'history'; // 提交后切换到历史记录
    isPreparingReSubmit.value = false; // 重置修改状态
  } catch (err) {
    console.error("Submit error:", err.response || err);
    ElMessage.error(err.response?.data?.detail || '提交失败，请检查网络或文件。');
  } finally {
    submitting.value = false;
  }
};


const loadInitialData = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const res = await fetchAssignmentInfo(props.id); // 这个接口应该返回作业信息及该学生的所有历史提交
    assignment.value = res.data; // { ...assignmentDetails, submissions: [...] }
    document.title = `${assignment.value.title || '作业'} - 提交`;

    // 找到学生当前有效的提交（最新的，或未被退回的，或教师已评分的）
    // 后端返回的 assignment.submissions 应该是该学生对此作业的所有提交记录
    if (assignment.value.submissions && assignment.value.submissions.length > 0) {
      // 通常取最后一次提交作为当前要显示的，除非有特殊逻辑
      // 按提交时间降序排序
      const sortedSubmissions = [...assignment.value.submissions].sort((a, b) => dayjs(b.submit_time).valueOf() - dayjs(a.submit_time).valueOf());
      mySubmissionDetails.value = sortedSubmissions[0]; // 最新一次提交
    } else {
      mySubmissionDetails.value = null;
    }

    // 根据mySubmissionDetails设置表单初始状态
    if (mySubmissionDetails.value) {
      form.value.comment = mySubmissionDetails.value.content || '';
      // files 不直接从 mySubmissionDetails.value.files 填充，因为它们是已上传文件的元数据，不是 File 对象
      // 用户需要重新选择文件进行修改
      form.value.files = [];
    } else {
      form.value.comment = '';
      form.value.files = [];
    }

  } catch (err) {
    console.error("Error loading assignment data:", err.response || err);
    loadError.value = err.response?.data?.detail || '无法加载作业信息，请稍后重试。';
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
};


const loadHistoryToForm = (submissionData) => {
  mySubmissionDetails.value = submissionData; // 更新当前显示的提交详情
  form.value.comment = submissionData.content || '';
  form.value.files = []; // 清空待上传文件列表
  // 提示用户文件需要重新选择
  ElMessage.info('已载入历史提交的文本内容。如需修改附件，请重新选择文件。');
  isPreparingReSubmit.value = true; // 进入修改模式
  activeTab.value = 'edit'; // 切换到编辑Tab
};

const handleDeleteSubmission = async (submissionId) => {
  try {
    await ElMessageBox.confirm('确定要撤回这条提交记录吗？撤回后不可恢复。', '撤回确认', {
      confirmButtonText: '确认撤回', cancelButtonText: '取消', type: 'warning',
    });
    await deleteDrawSubmission(submissionId);
    ElMessage.success('提交已成功撤回！');
    await loadInitialData(); // 重新加载数据以更新列表和状态
    // 如果撤回的是当前显示的 mySubmissionDetails，则清空它
    if (mySubmissionDetails.value && mySubmissionDetails.value.id === submissionId) {
      mySubmissionDetails.value = null;
      isPreparingReSubmit.value = false; // 退出修改模式
    }
  } catch (err) {
    if (err !== 'cancel') { // 用户点击取消时，confirm会reject 'cancel'
      console.error("Error deleting submission:", err.response || err);
      ElMessage.error(err.response?.data?.detail || '撤回提交失败。');
    }
  }
};


onMounted(loadInitialData);

</script>

<style scoped>
.assignment-container {
  max-width: 900px;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.assignment-header {
  text-align: center;
  padding-bottom: 16px;
  /* margin-bottom: 20px; */
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); /* Responsive cards */
  gap: 16px;
  margin: 24px 0;
}

.info-card {
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.info-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.info-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px; /* More vertical padding */
  text-align: center;
}

.info-icon {
  font-size: 28px; /* Larger icon */
  color: var(--el-color-primary);
  margin-bottom: 12px;
}

.info-title {
  font-size: 13px; /* Smaller title */
  color: #a0aec0; /* Lighter color */
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 16px; /* Adjusted size */
  font-weight: 500; /* Medium weight */
  color: #2d3748; /* Darker value */
}

.text-danger {
  color: #F56C6C;
}

.description-box, .comment-display-box {
  line-height: 1.7; /* Improved readability */
  font-size: 14px;
  color: #4a5568; /* Slightly darker text */
  word-break: break-word;
}

.comment-display-box {
  background-color: #f8fafc; /* Very light grey for comments */
  padding: 12px 15px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  min-height: 60px;
}

.bg-blue-50 {
  background-color: #eff6ff;
}

/* Example for AI comment background */


.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px; /* Adjusted padding */
  border-radius: 6px;
  background-color: #f7fafc; /* Lighter background */
  margin-bottom: 8px;
  border: 1px solid #e2e8f0; /* Light border */
  font-size: 14px;
  color: #4a5568;
}

.file-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quill-editor-wrapper { /* Added wrapper for better styling control */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden; /* To ensure border-radius applies to child toolbar/container */
}

:deep(.ql-toolbar.ql-snow) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  border-bottom: 1px solid #dcdfe6; /* Add border below toolbar */
}

:deep(.ql-container.ql-snow) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  font-size: 14px; /* Ensure editor font size */
  line-height: 1.6;
}

:deep(.ql-editor) {
  min-height: 120px; /* Adjusted min-height */
  padding: 10px 12px;
}

.el-upload__tip {
  line-height: 1.4;
  margin-top: 8px;
  font-size: 13px;
}

/* Markdown content styling (already provided, ensure it's applied correctly) */
.markdown-content :deep(pre) {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 1em;
  overflow: auto;
  border-radius: 5px;
  margin: 1em 0;
  font-family: 'Courier New', Courier, monospace;
}

.markdown-content :deep(code:not(.hljs)) {
  background-color: #eef1f5;
  color: #c0341d;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

.submission-info p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #333;
}

.submission-info .font-medium {
  color: #555;
}
</style>