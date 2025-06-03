<template>
  <div class="p-6 space-y-6">
    <el-tabs v-model="activeTab" class="custom-tabs">
      <el-tab-pane label="提交 / 编辑" name="edit" class="tab-pane-content">
        <div class="assignment-container p-2 md:p-6">
          <el-skeleton v-if="loading" animated :rows="6"/>

          <el-alert
              v-else-if="loadError"
              type="error"
              :closable="false"
              :title="loadError"
              show-icon
              class="mb-6"
          >
            <template #description>
              <p>请检查网络连接或稍后再试。如果问题持续，请联系管理员。</p>
            </template>
          </el-alert>

          <template v-else-if="assignment && Object.keys(assignment).length > 0">
            <div class="mb-6 flex items-center justify-between page-actions">
              <el-button
                  @click="$router.push('/student/assignments')"
                  plain>
                <el-icon class="mr-1">
                  <ArrowLeft/>
                </el-icon>
                返回作业列表
              </el-button>
              <el-tag
                  size="large"
                  :type="isOverdue ? 'danger' : 'success'"
                  effect="light"
              >
                {{ isOverdue ? '已截止' : '进行中' }}
              </el-tag>
            </div>

            <el-card class="mb-6 assignment-details-card" shadow="hover">
              <div class="assignment-header">
                <h1 class="text-2xl font-bold mb-2">{{ assignment.title }}</h1>
                <div class="text-gray-500 text-sm mb-4">《{{ assignment.course_class_name }}》</div>
              </div>

              <el-divider content-position="left">作业信息</el-divider>

              <div class="info-cards">
                <el-card class="info-card" shadow="never">
                  <div class="info-card-content">
                    <el-icon class="info-icon text-blue-500">
                      <Clock/>
                    </el-icon>
                    <div class="info-title">截止时间</div>
                    <div :class="{'text-red-600 font-semibold': isOverdue}" class="info-value">
                      {{ formatDateTime(assignment.due_date) }}
                    </div>
                    <el-tag v-if="!isOverdue" size="small" type="warning" effect="light" class="mt-2">
                      剩余 {{ remainingTime }}
                    </el-tag>
                  </div>
                </el-card>

                <el-card class="info-card" shadow="never">
                  <div class="info-card-content">
                    <el-icon class="info-icon text-green-500">
                      <Trophy/>
                    </el-icon>
                    <div class="info-title">满分</div>
                    <div class="info-value">{{ assignment.max_score }} 分</div>
                  </div>
                </el-card>

                <el-card class="info-card" shadow="never">
                  <div class="info-card-content">
                    <el-icon class="info-icon text-purple-500">
                      <Calendar/>
                    </el-icon>
                    <div class="info-title">发布时间</div>
                    <div class="info-value">{{ formatDateTime(assignment.deploy_date) }}</div>
                  </div>
                </el-card>

                <el-card class="info-card" shadow="never">
                  <div class="info-card-content">
                    <el-icon class="info-icon text-orange-500">
                      <User/>
                    </el-icon>
                    <div class="info-title">发布教师</div>
                    <div class="info-value">{{ assignment.deployer_name }}</div>
                  </div>
                </el-card>
              </div>

              <div class="mt-6">
                <div class="font-medium text-lg mb-2 flex items-center section-title">
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
                v-if="currentDisplaySubmission && (isEffectivelySubmitted(currentDisplaySubmission) || currentDisplaySubmission.is_returned)">
              <el-card class="mb-6 submission-status-card" shadow="hover">
                <template #header>
                  <div class="flex items-center justify-between">
                    <div class="flex items-center">
                      <el-icon :color="headerIconColor(currentDisplaySubmission)" class="mr-2">
                        <CircleCheckFilled
                            v-if="isEffectivelySubmitted(currentDisplaySubmission) && !currentDisplaySubmission.is_returned"/>
                        <WarningFilled v-if="currentDisplaySubmission.is_returned"/>
                        <InfoFilled
                            v-if="currentDisplaySubmission.ai_grading_status === 'processing' || currentDisplaySubmission.ai_grading_status === 'pending'"/>
                      </el-icon>
                      <span class="font-bold">我的当前提交状态: {{
                          getSubmissionStatusText(currentDisplaySubmission)
                        }}</span>
                    </div>
                    <el-button
                        v-if="!isOverdue || currentDisplaySubmission.is_returned"
                        type="primary"
                        plain
                        size="small"
                        @click="prepareReSubmit"
                        :disabled="submitting"
                    >
                      {{ currentDisplaySubmission.is_returned ? '修改并重新提交' : '编辑本次提交' }}
                    </el-button>
                  </div>
                </template>

                <div class="submission-info p-4 space-y-3">
                  <p><span class="font-medium text-gray-600">提交时间:</span>
                    {{ formatDateTime(currentDisplaySubmission.submit_time) }}</p>

                  <div v-if="getFinalScore(currentDisplaySubmission) !== null">
                    <span class="font-medium text-gray-600">我的得分:</span>
                    <el-tag :type="getScoreTagType(getFinalScore(currentDisplaySubmission))" effect="light" size="large"
                            class="ml-2">
                      {{ getFinalScore(currentDisplaySubmission) }} / {{ assignment.max_score }}
                    </el-tag>
                  </div>

                  <div v-if="getFinalComment(currentDisplaySubmission)">
                    <p class="font-medium text-gray-600 mb-1">教师/AI评语:</p>
                    <div class="comment-box markdown-content"
                         v-html="renderMarkdown(getFinalComment(currentDisplaySubmission))"></div>
                  </div>

                  <div
                      v-if="currentDisplaySubmission.ai_grading_status === 'completed' && typeof currentDisplaySubmission.ai_generated_similarity === 'number'">
                    <span class="font-medium text-gray-600">AI分析-内容疑似度:</span>
                    <el-progress
                        :percentage="Math.round(currentDisplaySubmission.ai_generated_similarity * 100)"
                        :stroke-width="10"
                        :format="(percentage) => `${percentage}%`"
                        style="width: 200px; display: inline-block; margin-left: 10px;"/>
                  </div>
                  <div v-if="currentDisplaySubmission.ai_grading_status === 'failed'">
                    <span class="font-medium text-gray-600">AI批改:</span>
                    <el-tag type="danger" effect="plain" class="ml-2">处理失败</el-tag>
                    <p v-if="currentDisplaySubmission.ai_comment" class="text-xs text-gray-500 mt-1">详情:
                      {{ currentDisplaySubmission.ai_comment }}</p>
                  </div>
                  <div v-if="currentDisplaySubmission.ai_grading_status === 'skipped'">
                    <span class="font-medium text-gray-600">AI批改:</span>
                    <el-tag type="warning" effect="plain" class="ml-2">已跳过</el-tag>
                    <p v-if="currentDisplaySubmission.ai_comment" class="text-xs text-gray-500 mt-1">原因:
                      {{ currentDisplaySubmission.ai_comment }}</p>
                  </div>


                  <div class="files-list mt-4" v-if="currentDisplaySubmission.files?.length">
                    <p class="font-medium text-gray-600 mb-2">我提交的文件:</p>
                    <div
                        v-for="file in currentDisplaySubmission.files"
                        :key="file.id || file.name"
                        class="file-item">
                      <el-icon class="text-gray-500">
                        <Paperclip/>
                      </el-icon>
                      <span class="text-sm">{{ file.name || file.original_name }}</span>
                    </div>
                  </div>
                </div>
              </el-card>
            </template>

            <el-card v-if="!isEffectivelySubmitted(currentDisplaySubmission) || editingCurrentSubmission" shadow="hover"
                     class="submit-form-card">
              <template #header>
                <div class="font-bold text-lg flex items-center section-title">
                  <el-icon class="mr-2">
                    <UploadFilled/>
                  </el-icon>
                  {{ editingCurrentSubmission ? '修改并提交作业' : '提交我的作业' }}
                </div>
              </template>

              <el-form ref="formRef" :model="form" label-position="top">
                <el-form-item label="作业附件 (必需)" prop="files">
                  <el-upload
                      ref="uploadRef"
                      v-model:file-list="form.files"
                      action="#"
                      :auto-upload="false"
                      :limit="3"
                      drag
                      multiple
                      :on-exceed="handleExceed"
                      :on-change="handleFileSelectionChange"
                      :on-remove="handleFileRemove"
                  >
                    <el-icon class="el-icon--upload">
                      <Upload/>
                    </el-icon>
                    <div class="el-upload__text">
                      将文件拖到此处，或 <em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip text-gray-500">
                        * 最多可上传3个文件，单个文件不超过10MB，总大小不超过50MB。支持常见代码/文本文件。
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>

                <el-form-item label="备注说明 (选填)">
                  <div class="quill-editor-wrapper">
                    <QuillEditor
                        v-model:content="form.comment"
                        contentType="html"
                        theme="snow"
                        :toolbar="editorToolbarOptions"
                        placeholder="可以在这里添加对作业的说明或心得体会..."
                        style="min-height: 150px;"
                    />
                  </div>
                </el-form-item>

                <el-form-item style="padding-top: 20px; text-align:center;">
                  <el-button
                      type="primary"
                      @click="handleSubmit"
                      :loading="submitting"
                      :disabled="isOverdue && !currentDisplaySubmission?.is_returned || form.files.length === 0"
                      size="large"
                  >
                    {{
                      (isOverdue && !currentDisplaySubmission?.is_returned) ? '已截止无法提交' : (editingCurrentSubmission ? '确认修改并提交' : '确认提交')
                    }}
                  </el-button>
                  <el-button @click="cancelEditOrGoBack" size="large">
                    {{ editingCurrentSubmission ? '取消修改' : '返回列表' }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </template>
          <el-empty v-else-if="!loading" description="作业信息加载失败或不存在。"/>
        </div>
      </el-tab-pane>

      <el-tab-pane label="历史提交记录" name="history" class="tab-pane-content">
        <submission-history-tab
            v-if="assignment && assignment.id"
            :assignment-id="assignment.id"
            :assignment-max-score="assignment.max_score"
            :key="historyTabKey"
            @view-submission-detail="handleViewHistoryDetail"
            @resubmit-history="handleResubmitHistory"
        />
        <el-empty v-else description="请先等待作业信息加载完毕。"/>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import {computed, nextTick, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import stuRequest from '@/utils/request_stu' // 确保使用正确的API请求实例
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn' // Ensure locale is imported
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ArrowLeft,
  Calendar,
  CircleCheckFilled,
  Clock,
  Document,
  InfoFilled,
  Paperclip,
  Trophy,
  Upload,
  UploadFilled,
  User,
  WarningFilled
} from '@element-plus/icons-vue'
import {fetchAssignmentInfo} from '@/api/student.js' // updateSubmission 对应 PATCH
import {QuillEditor} from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

import SubmissionHistoryTab from '@/views/student/SubmissionHistoryTab.vue' // 确保路径正确

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const props = defineProps({id: {type: [String, Number], required: true}})
const router = useRouter()
const route = useRoute()

const activeTab = ref('edit')
const loading = ref(true)
const loadError = ref('')
const assignment = ref({}) // 存储作业详情及其所有提交记录
const currentDisplaySubmission = ref(null) // 当前用于在“编辑”tab页显示的提交（通常是最新的有效提交）

const formRef = ref()
const uploadRef = ref() // Ref for el-upload
const form = ref({
  files: [], // 用于el-upload的v-model:file-list
  rawFiles: [], // 存储实际的File对象
  comment: '',
  title: '', // 提交的标题，可以考虑从作业标题预填充
})

const submitting = ref(false)
const editingCurrentSubmission = ref(false) // 标记是否正在编辑当前提交
const historyTabKey = ref(0) // 用于强制刷新历史记录组件

const md = new MarkdownIt({html: true, linkify: true, typographer: true});
const renderMarkdown = (text) => text ? DOMPurify.sanitize(md.render(text)) : '';

const editorToolbarOptions = [
  ['bold', 'italic', 'underline'], ['blockquote', 'code-block'],
  [{'list': 'ordered'}, {'list': 'bullet'}],
  [{'header': [1, 2, 3, false]}],
  ['link'], ['clean']
];


const isOverdue = computed(() => {
  if (!assignment.value?.due_date) return false;
  return dayjs(assignment.value.due_date).isBefore(dayjs());
});

const formattedDescription = computed(() => {
  if (!assignment.value?.description) return '';
  return renderMarkdown(assignment.value.description);
});

const remainingTime = computed(() => {
  if (!assignment.value?.due_date) return '';
  const now = dayjs();
  const due = dayjs(assignment.value.due_date);
  if (due.isBefore(now)) return '已截止';
  return due.fromNow(true); // 'xx 分钟/小时/天'
});

// 判断一个提交是否是“有效”的，即已提交且未被退回
const isEffectivelySubmitted = (submission) => {
  return submission && submission.submitted && !submission.is_returned;
};

const getFinalScore = (submission) => {
  if (!submission) return null;
  if (submission.score !== null && typeof submission.score !== 'undefined') {
    return submission.score;
  }
  if (submission.ai_grading_status === 'completed' && submission.ai_score !== null && typeof submission.ai_score !== 'undefined') {
    return submission.ai_score;
  }
  return null;
};

const getFinalComment = (submission) => {
  if (!submission) return '';
  if (submission.teacher_comment) {
    return submission.teacher_comment;
  }
  if (submission.ai_grading_status === 'completed' && submission.ai_comment) {
    return submission.ai_comment;
  }
  return '';
};

const getSubmissionStatusText = (submission) => {
  if (!submission) return '未提交';
  const finalScore = getFinalScore(submission);

  if (submission.is_returned) return '已退回 (待重交)';
  if (isEffectivelySubmitted(submission)) {
    if (finalScore !== null) return `已评分 (${finalScore})`;
    if (submission.ai_grading_status === 'processing') return 'AI批改中...';
    if (submission.ai_grading_status === 'pending') return '已提交 (等待AI批改)';
    return '已提交 (待批改)';
  }
  // 如果不是有效提交（例如仅保存但未标记submitted，或ai_grading_status是skipped/failed且无教师评分）
  // 或者已截止但未提交过
  if (isOverdue.value) return '已截止 (未提交)';
  return '待提交';
};

const getScoreTagType = (score) => {
  if (score === null || typeof score === 'undefined') return 'info';
  const numericScore = parseFloat(score);
  const maxScore = parseFloat(assignment.value?.max_score || 100);
  if (numericScore >= maxScore * 0.85) return 'success';
  if (numericScore >= maxScore * 0.6) return 'warning';
  return 'danger';
};

const headerIconColor = (submission) => {
  if (!submission) return '#909399'; // Info for '未提交'
  if (submission.is_returned) return '#E6A23C'; // Warning
  if (isEffectivelySubmitted(submission)) {
    const finalScore = getFinalScore(submission);
    if (finalScore !== null) return '#67C23A'; // Success
    if (submission.ai_grading_status === 'processing' || submission.ai_grading_status === 'pending') return '#409EFF'; // Primary
    return '#67C23A'; // Success for submitted but not yet graded by AI/Teacher
  }
  return '#909399';
};


const formatDateTime = (dateString) => {
  if (!dateString) return '未知';
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
};

const handleFileSelectionChange = (file, fileList) => {
  // fileList是el-upload内部维护的列表，包含 File 对象
  // 我们需要将实际的File对象存储起来用于FormData
  form.value.rawFiles = fileList.map(f => f.raw).filter(f => f instanceof File);

  // 文件大小检查 (单个文件)
  const singleFileMaxSize = 10 * 1024 * 1024; // 10MB
  if (file.size > singleFileMaxSize) {
    ElMessage.warning(`文件 ${file.name} 大小超过10MB限制`);
    // 从列表中移除超大文件
    form.value.files = form.value.files.filter(f => f.uid !== file.uid);
    form.value.rawFiles = form.value.rawFiles.filter(f => f.name !== file.name || f.size !== file.size); // 简单匹配
    uploadRef.value?.handleRemove(file); // 调用el-upload的移除方法更新UI
    return false;
  }

  // 总文件大小检查
  const totalSize = form.value.rawFiles.reduce((sum, f) => sum + f.size, 0);
  const totalMaxSize = 50 * 1024 * 1024; // 50MB
  if (totalSize > totalMaxSize) {
    ElMessage.warning('所有文件总大小不能超过50MB');
    // 移除刚添加的文件
    form.value.files = form.value.files.filter(f => f.uid !== file.uid);
    form.value.rawFiles = form.value.rawFiles.filter(f => f.name !== file.name || f.size !== file.size);
    uploadRef.value?.handleRemove(file);
    return false;
  }
  return true;
};

const handleFileRemove = (file, fileList) => {
  form.value.rawFiles = fileList.map(f => f.raw).filter(f => f instanceof File);
};


const handleExceed = () => {
  ElMessage.warning('最多只能上传3个文件');
};

const loadAssignmentData = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const res = await fetchAssignmentInfo(props.id); // 这个API现在应该返回作业详情和所有提交记录
    assignment.value = res.data;
    document.title = `${assignment.value.title || '作业'} - 提交`;

    // 确定当前显示的提交 (通常是最新的有效提交，或退回的提交)
    if (assignment.value.submissions && assignment.value.submissions.length > 0) {
      // 优先找未被退回的最新提交，其次是最新被退回的提交
      const nonReturned = assignment.value.submissions.filter(s => !s.is_returned).sort((a, b) => dayjs(b.submit_time).valueOf() - dayjs(a.submit_time).valueOf());
      const returned = assignment.value.submissions.filter(s => s.is_returned).sort((a, b) => dayjs(b.submit_time).valueOf() - dayjs(a.submit_time).valueOf());

      currentDisplaySubmission.value = nonReturned.length > 0 ? nonReturned[0] : (returned.length > 0 ? returned[0] : null);

      // 如果当前显示的提交是被退回的，则自动进入编辑模式
      if (currentDisplaySubmission.value && currentDisplaySubmission.value.is_returned && !isOverdue.value) {
        prepareReSubmit();
      }

    } else {
      currentDisplaySubmission.value = null;
    }

    // 刷新历史记录tab
    historyTabKey.value++;

  } catch (err) {
    console.error("Error loading assignment data:", err);
    loadError.value = err.response?.data?.detail || err.message || '加载作业信息失败';
    if (err.response?.status === 404) {
      loadError.value = '未找到该作业或您没有权限访问。';
    }
  } finally {
    loading.value = false;
  }
};

const prepareReSubmit = () => {
  if (currentDisplaySubmission.value) {
    form.value.title = currentDisplaySubmission.value.title || ''; // 实际上学生提交的title可能没用
    form.value.comment = currentDisplaySubmission.value.content || ''; // 假设旧的content是学生评语
    form.value.files = []; // 清空旧文件列表，要求学生重新上传
    form.value.rawFiles = [];
    if (uploadRef.value) {
      uploadRef.value.clearFiles(); // 清空el-upload组件中的文件
    }
  } else { // 如果没有当前提交 (例如首次提交)
    form.value.title = assignment.value?.title || '';
    form.value.comment = '';
    form.value.files = [];
    form.value.rawFiles = [];
  }
  editingCurrentSubmission.value = true; // 进入编辑/提交表单的显示状态
};

const cancelEditOrGoBack = () => {
  if (editingCurrentSubmission.value) {
    editingCurrentSubmission.value = false; // 取消编辑，回到查看状态（如果之前有提交）
    form.value.files = []; // 清空选择
    form.value.rawFiles = [];
    if (uploadRef.value) {
      uploadRef.value.clearFiles();
    }
  } else {
    router.push('/student/assignments');
  }
};

const handleSubmit = async () => {
  if (form.value.rawFiles.length === 0) {
    ElMessage.warning('请至少选择一个文件提交');
    return;
  }
  if (isOverdue.value && !(currentDisplaySubmission.value?.is_returned)) {
    ElMessage.error('该作业已截止，无法提交。如需补交，请联系老师申请。');
    return;
  }

  try {
    await ElMessageBox.confirm(
        `确定要${editingCurrentSubmission.value && currentDisplaySubmission.value ? '修改并' : ''}提交作业吗？`,
        '提交确认', {confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning'}
    );
  } catch {
    return; // 用户取消
  }

  const fd = new FormData();
  // assignmentId 是从 props.id 获取的，是作业本身的ID
  fd.append("assignment", props.id); // 后端 AssignmentSubmissionView create 时需要 assignment ID
  fd.append('title', form.value.title || `${assignment.value.title} - 提交`); // 学生提交的标题
  fd.append('content', form.value.comment || ''); // 学生提交的备注/内容

  form.value.rawFiles.forEach(file => {
    fd.append('files', file); // 'files' 对应后端 request.FILES.getlist('files')
  });

  submitting.value = true;
  try {
    // 如果 currentDisplaySubmission 存在且 editingCurrentSubmission 为 true，说明是“修改提交”
    // 实际上，后端的 create 逻辑处理了覆盖，所以这里统一调用 create
    // 你的后端 AssignmentSubmissionView.create 已经处理了删除旧提交的逻辑，所以总是 "创建" 新的
    await stuRequest.post(`/assignments/${props.id}/submissions/`, fd, { // 使用 /cou/student 前缀的 stuRequest
      headers: {'Content-Type': 'multipart/form-data'}
    });
    ElMessage.success('作业提交成功！');
    editingCurrentSubmission.value = false; // 退出编辑模式
    form.value.files = []; // 清空文件列表
    form.value.rawFiles = [];
    if (uploadRef.value) {
      uploadRef.value.clearFiles();
    }
    await loadAssignmentData(); // 重新加载数据以显示最新提交和AI状态
  } catch (err) {
    console.error("Submission error:", err.response || err);
    ElMessage.error(err.response?.data?.detail || '作业提交失败，请稍后重试。');
  } finally {
    submitting.value = false;
  }
};

// 从历史记录子组件触发的事件
const handleViewHistoryDetail = (submissionDetail) => {
  // 当用户在历史记录中点击查看某个旧提交时，我们可以更新 currentDisplaySubmission
  // 使得主编辑区域显示这个旧提交的详细信息，但保持表单为不可编辑状态
  currentDisplaySubmission.value = submissionDetail;
  editingCurrentSubmission.value = false; // 确保不是编辑模式
  activeTab.value = 'edit'; // 切换回编辑/查看tab
  nextTick(() => {
    window.scrollTo({top: 0, behavior: 'smooth'}); // 滚动到页面顶部
  });
};

const handleResubmitHistory = (submissionToResubmit) => {
  // 当用户从历史记录选择一个提交来“重新提交”
  currentDisplaySubmission.value = submissionToResubmit; // 可以用来预填一些信息，或者只是作为参考
  prepareReSubmit(); // 进入编辑模式，表单内容可以基于 submissionToResubmit 预设
  activeTab.value = 'edit';
  nextTick(() => {
    window.scrollTo({top: 0, behavior: 'smooth'});
  });
};


onMounted(loadAssignmentData);

</script>

<style scoped>
.assignment-container {
  max-width: 900px;
  margin: 0 auto;
  background-color: #f9fafb;
  border-radius: 8px;
}

.page-actions {
  padding: 10px 0;
}

.assignment-details-card, .submission-status-card, .submit-form-card {
  border: 1px solid #e4e7ed;
  background-color: #fff;
}

.assignment-header {
  text-align: center;
  padding-bottom: 16px;
}

.assignment-header .text-gray-500 {
  color: #909399;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin: 24px 0;
}

.info-card {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
}

.info-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 10px;
  text-align: center;
}

.info-icon {
  font-size: 28px;
  margin-bottom: 10px;
}

.info-icon.text-blue-500 {
  color: #409EFF;
}

.info-icon.text-green-500 {
  color: #67C23A;
}

.info-icon.text-purple-500 {
  color: #a06eff;
}

.info-icon.text-orange-500 {
  color: #E6A23C;
}


.info-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.info-value {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.info-value.text-red-600 {
  color: #F56C6C;
}

.section-title {
  color: #303133;
  border-bottom: 2px solid var(--el-color-primary-light-5);
  padding-bottom: 8px;
  margin-bottom: 16px;
}

.description-box {
  line-height: 1.7;
  color: #303133;
  font-size: 14px;
  padding: 16px;
  background-color: #fdfdfd;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  white-space: pre-wrap; /* 保留换行和空格 */
}

.markdown-content :deep(p) {
  margin-bottom: 0.5em;
}

/* 调整 Markdown 内部元素间距 */


.submission-status-card .el-card__header {
  background-color: #f5f7fa;
}

.submission-info {
  font-size: 14px;
  color: #606266;
}

.submission-info .font-medium {
  color: #303133;
}

.comment-box {
  background-color: #f9fafb;
  border: 1px solid #e4e7ed;
  padding: 12px 15px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
  min-height: 60px;
  white-space: pre-wrap; /* 保留换行和空格 */
}

.markdown-content :deep(h1), .markdown-content :deep(h2), .markdown-content :deep(h3) {
  margin-top: 0.8em;
  margin-bottom: 0.4em;
}


.files-list {
  margin-top: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 4px;
  background-color: #f0f2f5;
  margin-bottom: 6px;
  font-size: 13px;
  color: #303133;
}

.file-item .el-icon {
  font-size: 16px;
}

.submit-form-card .el-card__header {
  background-color: #f5f7fa;
}

.quill-editor-wrapper {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

:deep(.ql-toolbar.ql-snow) {
  border-bottom: 1px solid #dcdfe6;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

:deep(.ql-container.ql-snow) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  font-size: 14px;
  min-height: 120px;
}

:deep(.el-tabs__header) {
  margin-bottom: 0; /* 移除tabs header下方的默认margin */
}

.tab-pane-content {
  padding-top: 20px; /* 为tab内容区域增加上边距 */
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none; /* 移除 Element Plus Tabs 默认的下边框 */
}

.custom-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  padding: 0 25px; /* 增加 tab 的横向 padding */
  height: 50px; /* 增加 tab 的高度 */
  line-height: 50px;
}

.custom-tabs :deep(.el-tabs__active-bar) {
  height: 3px; /* 加粗激活状态的下划线 */
}

</style>