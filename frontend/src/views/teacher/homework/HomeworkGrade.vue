<template>
  <div class="grade-page-container">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <div class="header-content">
          <span class="text-xl font-semibold">
            批改作业：{{ submissionData.assignment?.title || '加载中...' }}
          </span>
          <el-tag v-if="submissionData.student?.name" effect="light" size="small" round class="ml-2">
            {{ submissionData.student.name }} ({{ submissionData.student.student_number }})
          </el-tag>
        </div>
      </template>
    </el-page-header>

    <div v-if="loadingSubmission" class="loading-state">
      <el-skeleton :rows="10" animated/>
    </div>

    <el-row :gutter="20" v-else-if="submissionData.id">
      <el-col :xs="24" :md="12" class="submission-column">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon>
                <Document/>
              </el-icon>
              <span>学生提交详情</span>
            </div>
          </template>
          <div class="submission-details">
            <p><strong>提交标题：</strong> {{ submissionData.title || '(学生未填写标题)' }}</p>
            <p>
              <strong>提交时间：</strong>
              <el-tag type="info" effect="plain" size="small">
                {{ dayjs(submissionData.submit_time).format('YYYY-MM-DD HH:mm:ss') }}
              </el-tag>
            </p>
            <el-divider/>

            <h4 class="section-title">提交文本内容：</h4>
            <div v-if="submissionData.content" v-html="renderMarkdown(submissionData.content)"
                 class="markdown-viewer"></div>
            <el-empty v-else description="学生未提交任何文本内容" :image-size="60"/>

            <div v-if="submissionData.files && submissionData.files.length > 0">
              <el-divider/>
              <h4 class="section-title">提交附件 ({{ submissionData.files.length }}):</h4>
              <div v-if="imageFiles.length" class="image-preview-grid">
                <el-image
                    v-for="(img, index) in imageFiles"
                    :key="img.id || img.url"
                    :src="img.url"
                    :preview-src-list="imageFiles.map(f => f.url)"
                    :initial-index="index"
                    fit="cover"
                    class="preview-thumbnail"
                    lazy
                    hide-on-click-modal
                    preview-teleported
                />
              </div>
              <div v-if="otherFiles.length" class="attachment-list">
                <el-link
                    v-for="file in otherFiles"
                    :key="file.id || file.url"
                    :href="file.url"
                    target="_blank"
                    type="primary"
                    class="attachment-item"
                    :underline="true"
                >
                  <el-icon class="el-icon--left">
                    <Paperclip/>
                  </el-icon>
                  {{ file.original_name || file.file_name }}
                </el-link>
              </div>
            </div>
            <el-empty
                v-if="!submissionData.content && (!submissionData.files || submissionData.files.length === 0)"
                description="学生未提交任何附件或文本内容"
                :image-size="80"
                class="mt-4"
            />
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12" class="grading-column">

        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon>
                <MagicStick/>
              </el-icon>
              <span>AI 辅助批改建议</span>
              <el-tag :type="aiStatusTagType" effect="light" size="small" round>{{ aiStatusText }}</el-tag>
            </div>
          </template>
          <div
              v-if="submissionData.ai_grading_status === 'completed' && (submissionData.ai_score !== null || submissionData.ai_comment)">
            <el-descriptions :column="1" border size="small" class="ai-descriptions">
              <el-descriptions-item label="AI 建议分数" v-if="submissionData.ai_score !== null">
                <el-tag :type="getScoreTagType(submissionData.ai_score, submissionData.assignment?.max_score)"
                        size="medium" effect="dark">
                  {{ submissionData.ai_score }} / {{ submissionData.assignment?.max_score || 100 }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="AI 建议评语" label-class-name="ai-comment-label">
                <div v-if="submissionData.ai_comment" v-html="renderMarkdown(submissionData.ai_comment)"
                     class="markdown-viewer ai-comment"></div>
                <span v-else class="text-gray-500 italic">AI未提供评语。</span>
              </el-descriptions-item>
              <el-descriptions-item label="AI 内容疑似度"
                                    v-if="typeof submissionData.ai_generated_similarity === 'number'">
                <el-progress
                    :percentage="Math.round(submissionData.ai_generated_similarity * 100)"
                    :stroke-width="10"
                    :format="(percentage) => `${percentage}%`"
                    class="similarity-progress"
                />
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div
              v-else-if="submissionData.ai_grading_status === 'failed' || submissionData.ai_grading_status === 'skipped'"
              class="ai-feedback-alert">
            <el-alert :title="`AI批改${submissionData.ai_grading_status === 'failed' ? '失败' : '已跳过'}`"
                      :description="submissionData.ai_comment || '无详细信息'" type="warning" show-icon
                      :closable="false"/>
          </div>
          <div
              v-else-if="submissionData.ai_grading_status === 'processing' || submissionData.ai_grading_status === 'pending'"
              class="ai-feedback-alert text-center">
            <div class="flex items-center justify-center text-gray-600">
              <el-icon class="is-loading mr-2" :size="18">
                <Loading/>
              </el-icon>
              <span>AI批改处理中，请稍后...</span>
            </div>
          </div>
          <el-empty v-else description="AI辅助批改未启用或暂无建议" :image-size="60"/>
        </el-card>


        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <el-icon>
                <EditPen/>
              </el-icon>
              <span>教师评分与评语</span>
            </div>
          </template>
          <el-form :model="gradingForm" ref="gradingFormRef" label-position="top" class="grading-form">
            <el-form-item label="最终分数" prop="score" :rules="scoreRules">
              <el-input-number
                  v-model="gradingForm.score"
                  :min="0"
                  :max="parseFloat(submissionData.assignment?.max_score || 100)"
                  controls-position="right"
                  class="w-full"
                  :disabled="gradingForm.isReturned"
              />
              <span class="form-item-tip">满分: {{ submissionData.assignment?.max_score || 100 }}</span>
            </el-form-item>

            <el-form-item label="最终评语" prop="comment">
              <QuillEditor
                  v-model:content="gradingForm.comment"
                  contentType="html"
                  theme="snow"
                  :toolbar="toolbarOptions"
                  placeholder="请输入您的最终评语（必填）..."
                  class="quill-editor-custom"
                  style="min-height: 150px; width: 100%;"
              />
            </el-form-item>

            <el-form-item label=" " prop="isReturned">
              <el-switch
                  v-model="gradingForm.isReturned"
                  @change="handleReturnChange"
                  active-text="退回"
                  inactive-text="不退回"
              />
              <el-tooltip
                  content="开启后，本次评分将无效，学生需要重新提交。系统会自动填充“作业已退回”作为评语，您也可以修改。"
                  placement="top">
                <el-icon class="ml-2 cursor-pointer text-gray-400">
                  <QuestionFilled/>
                </el-icon>
              </el-tooltip>
            </el-form-item>

            <el-form-item class="form-actions">
              <el-button @click="goBack" :icon="CloseBold">取消</el-button>
              <el-button type="primary" :loading="saving" @click="submitGrade" :icon="Select" size="large">
                {{ saving ? '正在保存...' : '保存批改' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-else-if="!loadingSubmission && !submissionData.id" description="未能加载到作业提交数据，请返回重试。"
              class="loading-state">
      <el-button type="primary" @click="goBack">返回上一页</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import {ref, onMounted, computed, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import dayjs from 'dayjs' //
import {gradeSubmission} from '@/api/homeworks' //
import couRequest from '@/utils/request_cou' //
import {ElMessage, ElMessageBox} from 'element-plus' //
import {
  Document,
  Paperclip,
  MagicStick,
  EditPen,
  Loading,
  QuestionFilled,
  Select,
  CloseBold
} from '@element-plus/icons-vue'
import {QuillEditor} from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const route = useRoute() //
const router = useRouter() //
const subId = route.params.subId //

const loadingSubmission = ref(true) //
const submissionData = ref({ //
  title: '', //
  content: '', //
  files: [], //
  student: {name: '', student_number: ''}, //
  assignment: {title: '', max_score: 100, ai_grading_enabled: false}, //
  submit_time: '', //
  score: null, //
  teacher_comment: '', //
  is_returned: false, //
  ai_score: null, //
  ai_comment: '', //
  ai_generated_similarity: null, //
  ai_grading_status: null, //
})

const gradingFormRef = ref(null) //
const gradingForm = ref({ //
  score: null, //
  comment: '', //
  isReturned: false //
})
const saving = ref(false) //

const md = new MarkdownIt({html: true, linkify: true, typographer: true}); //
const renderMarkdown = (text) => { //
  if (!text) return '';
  // 先进行Markdown到HTML的转换，然后清理HTML
  const rawHtml = md.render(text);
  return DOMPurify.sanitize(rawHtml, {USE_PROFILES: {html: true}});
};

const toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],        // 加粗, 斜体, 下划线, 删除线
  ['blockquote', 'code-block'],                      // 引用, 代码块

  [{'header': 1}, {'header': 2}],               // 标题1, 标题2
  [{'list': 'ordered'}, {'list': 'bullet'}],     // 有序列表, 无序列表
  [{'script': 'sub'}, {'script': 'super'}],      // 下标, 上标
  [{'indent': '-1'}, {'indent': '+1'}],          // 缩进
  [{'direction': 'rtl'}],                         // 文字方向

  [{'size': ['small', false, 'large', 'huge']}],  // 字号
  [{'header': [1, 2, 3, 4, 5, 6, false]}],

  [{'color': []}, {'background': []}],          // 颜色, 背景色
  [{'font': []}],                                 // 字体
  [{'align': []}],                                // 对齐方式

  ['clean'],                                         // 清除格式
  ['link', 'image']                                  // 链接, 图片 (如果需要)
];


const imageFiles = computed(() => //
    submissionData.value.files?.filter(f => f && f.original_name && /\.(jpg|jpeg|png|gif|webp|avif|svg)$/i.test(f.original_name)) || []
)
const otherFiles = computed(() => //
    submissionData.value.files?.filter(f => f && f.original_name && !/\.(jpg|jpeg|png|gif|webp|avif|svg)$/i.test(f.original_name)) || []
)

const aiStatusText = computed(() => { //
  switch (submissionData.value.ai_grading_status) {
    case 'completed':
      return 'AI建议已生成';
    case 'processing':
      return 'AI处理中';
    case 'pending':
      return '等待AI处理';
    case 'failed':
      return 'AI处理失败';
    case 'skipped':
      return 'AI已跳过';
    default:
      return submissionData.value.assignment?.ai_grading_enabled ? '状态未知' : 'AI未启用';
  }
});

const aiStatusTagType = computed(() => { //
  switch (submissionData.value.ai_grading_status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'primary';
    case 'pending':
      return 'info';
    case 'failed':
      return 'danger';
    case 'skipped':
      return 'warning';
    default:
      return 'info';
  }
});

const getScoreTagType = (score, maxScore = 100) => { //
  if (score === null || typeof score === 'undefined') return 'info';
  const numericScore = parseFloat(score);
  if (isNaN(numericScore)) return 'info';
  const numericMaxScore = parseFloat(maxScore);
  if (isNaN(numericMaxScore) || numericMaxScore === 0) return 'info'; // 避免除以0或NaN

  const ratio = numericScore / numericMaxScore;
  if (ratio >= 0.85) return 'success';
  if (ratio >= 0.6) return 'warning';
  return 'danger';
};

const handleReturnChange = (isReturned) => { //
  if (isReturned) {
    gradingForm.value.score = null; // 退回时，教师评分清空
    if (!gradingForm.value.comment) { // 如果评语为空，自动填充
      gradingForm.value.comment = '<p>作业已退回，请根据反馈修改后重新提交。</p>';
    }
    ElMessage.info('已选择退回重做，学生需要重新提交。评分已清空。');
  } else {
    // 如果从退回状态改回不退回，可以考虑恢复之前的分数（如果业务需要）
    // gradingForm.value.score = submissionData.value.score ?? null; // 或者保持为null让教师重新打分
  }
}


const fetchSubmissionDetails = async () => {
  loadingSubmission.value = true;
  try {
    const {data} = await couRequest.get(`/homeworks/submissions/${subId}/`) //
    // 将 assignment 对象直接赋值给 submissionData.assignment
    // 后端返回的 homeworks/submissions/:id/ 接口应该包含 assignment 的详细信息
    // 如果不是，则需要确保 submissionData.assignment 被正确填充
    submissionData.value = {
      ...data,
      // 确保 assignment 字段存在且包含所需属性
      assignment: data.assignment_details || data.assignment || {
        title: '未知作业',
        max_score: 100,
        ai_grading_enabled: false
      }
    };

    console.log('作业提交详情:', submissionData.value.ai_comment);


    // 初始化教师的评分表单
    // 优先使用教师已有的评分和评语
    gradingForm.value.score = data.score !== null ? parseFloat(data.score) : null;
    gradingForm.value.comment = data.teacher_comment || '';
    gradingForm.value.isReturned = data.is_returned || false;

    // 如果开启了AI批改，但教师尚未评分，可以考虑是否用AI分数预填充（通常不推荐直接填充，仅供参考）
    // if (submissionData.value.assignment?.ai_grading_enabled && data.score === null && data.ai_score !== null) {
    //   // gradingForm.value.score = parseFloat(data.ai_score); // 酌情决定是否预填充
    // }
    // if (submissionData.value.assignment?.ai_grading_enabled && !data.teacher_comment && data.ai_comment) {
    //   // gradingForm.value.comment = data.ai_comment; // 酌情决定是否预填充
    // }


  } catch (error) {
    console.error('获取作业提交详情失败:', error);
    ElMessage.error('获取作业数据失败，请返回重试。');
    // router.back();
  } finally {
    loadingSubmission.value = false;
  }
};

onMounted(fetchSubmissionDetails);


const scoreRules = [ //
  {
    validator: (rule, value, callback) => {
      if (gradingForm.value.isReturned) {
        callback();
        return;
      }
      const maxScore = parseFloat(submissionData.value.assignment?.max_score || 100);
      if (value === null || typeof value === 'undefined' || value === '') {
        callback(new Error('最终分数不能为空'));
      } else if (isNaN(parseFloat(value))) {
        callback(new Error('分数必须是数字'));
      } else if (value < 0 || value > maxScore) {
        callback(new Error(`分数必须在 0 到 ${maxScore} 之间`));
      } else {
        callback();
      }
    },
    trigger: ['blur', 'change']
  }
];


const submitGrade = async () => { //
  if (!gradingFormRef.value) return;
  gradingFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请检查评分表单是否完整且有效。');
      return;
    }
    if (!gradingForm.value.isReturned && (!gradingForm.value.comment || gradingForm.value.comment === '<p><br></p>')) {
      ElMessageBox.confirm(
          '您没有填写任何评语，确定要直接保存评分吗？',
          '评语确认',
          {
            confirmButtonText: '确定保存',
            cancelButtonText: '去填写评语',
            type: 'warning',
          }
      ).then(async () => {
        await proceedWithSave();
      }).catch(() => {
        ElMessage.info('已取消保存，请填写评语。');
      });
    } else {
      await proceedWithSave();
    }
  });
};

const proceedWithSave = async () => {
  saving.value = true;
  const payload = {
    score: gradingForm.value.isReturned ? null : gradingForm.value.score,
    teacher_comment: gradingForm.value.comment || (gradingForm.value.isReturned ? '<p>作业已退回，请修改后重新提交。</p>' : '<p>已批改。</p>'), // 确保HTML格式
    is_returned: gradingForm.value.isReturned
  };

  try {
    await gradeSubmission(subId, payload); //
    ElMessage.success('批改结果保存成功！');
    router.back(); //
  } catch (error) {
    console.error('保存批改失败:', error);
    ElMessage.error('保存批改失败：' + (error.response?.data?.detail || error.message || '网络错误'));
  } finally {
    saving.value = false;
  }
}

const goBack = () => {
  router.back();
};

</script>

<style scoped>
.grade-page-container {
  padding: 20px;
  background-color: #f4f7f9; /* 更柔和的背景色 */
}

.page-header {
  background-color: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  align-items: center;
}

.loading-state {
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
}

.panel-card {
  margin-bottom: 20px;
  border-radius: 8px; /* 圆角 */
  border: 1px solid var(--el-border-color-lighter); /* 统一边框 */
}

.panel-card .el-card__header {
  background-color: var(--el-fill-color-lighter); /* 头部背景色 */
  padding: 12px 18px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between; /* 让标签靠右 */
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.panel-header .el-icon {
  margin-right: 8px;
  font-size: 18px; /* 头部图标稍大 */
}

.submission-details {
  padding: 18px;
}

.submission-details p {
  margin-bottom: 10px;
  font-size: 14px;
  color: #555;
  line-height: 1.6;
}

.submission-details strong {
  color: #333;
  margin-right: 6px;
}

.section-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-top: 16px;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}

.markdown-viewer {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  background-color: #fff;
  padding: 12px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  min-height: 80px; /* 最小高度 */
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.markdown-viewer :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-viewer :deep(pre) {
  background-color: #f5f7fa;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
  border: 1px solid var(--el-border-color-lighter);
}

.markdown-viewer :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
  background-color: #f0f2f5;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 0.9em;
}

.markdown-viewer :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: inherit;
}

.markdown-viewer :deep(blockquote) {
  border-left: 3px solid var(--el-color-primary-light-5);
  padding-left: 1em;
  color: #5f6368;
  margin: 1em 0;
  background-color: var(--el-color-primary-light-9);
}


.image-preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.preview-thumbnail {
  width: 100%;
  height: 80px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  object-fit: cover; /* 保证图片不变形 */
  cursor: pointer;
}

.attachment-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  font-size: 14px;
  transition: color 0.2s;
}

.attachment-item:hover {
  color: var(--el-color-primary-dark-2);
}

.attachment-item .el-icon {
  vertical-align: text-bottom;
}

.ai-descriptions {
  font-size: 14px;
}

.ai-descriptions :deep(.el-descriptions__label.ai-comment-label) {
  vertical-align: top; /* 确保评语较长时标签顶部对齐 */
}

.ai-comment {
  max-height: 150px; /* AI评语过长时可滚动 */
  overflow-y: auto;
}

.similarity-progress {
  max-width: 250px; /* 限制进度条宽度 */
  margin-top: 4px;
}

.ai-feedback-alert {
  padding: 15px;
}

.grading-form {
  padding: 10px 0; /* 表单区域的内边距 */
}

.grading-form .el-form-item {
  margin-bottom: 22px;
}

.grading-form .form-item-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.quill-editor-custom :deep(.ql-toolbar) {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
  background-color: #fdfdfd;
}

.quill-editor-custom :deep(.ql-container) {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
  min-height: 120px; /* 编辑器最小高度 */
  font-size: 14px;
}

.form-actions {
  margin-top: 28px;
  display: flex;
  justify-content: flex-end; /* 按钮靠右 */
}

.form-actions .el-button {
  min-width: 100px; /* 按钮最小宽度 */
}

.panel-card-placeholder {
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  background-color: #fff;
  border: 1px solid var(--el-border-color-lighter);
}

.quill-editor-container {
  width: 100%; /* 确保容器占据其父el-form-item的全部宽度 */
  border: 1px solid var(--el-border-color-light); /* 给整个编辑器一个边框 */
  border-radius: var(--el-border-radius-base); /* 统一圆角 */
  overflow: hidden; /* 防止内部元素溢出破坏圆角 */
}

.quill-editor-custom {
  /* style="min-height: 150px;" 已在template中设置，这里可以不用重复 */
}

/* 使用 :deep() 穿透 scoped CSS 来修改 QuillEditor 内部样式 */
.quill-editor-container :deep(.ql-toolbar.ql-snow) {
  border-top-left-radius: var(--el-border-radius-base); /* 匹配容器圆角 */
  border-top-right-radius: var(--el-border-radius-base);
  border: none; /* 移除工具栏自身的顶边框和左右边框，由外部容器控制 */
  border-bottom: 1px solid var(--el-border-color-light); /* 工具栏和内容区之间的分割线 */
  padding: 8px 8px; /* 调整工具栏内边距 */
  background-color: #f9fafb; /* 工具栏背景色 */
  /* 确保工具栏宽度和内容区一致，通常 Quill 默认会处理好，
     但如果出现问题，可以尝试 width: 100% */
}

.quill-editor-container :deep(.ql-container.ql-snow) {
  border-bottom-left-radius: var(--el-border-radius-base); /* 匹配容器圆角 */
  border-bottom-right-radius: var(--el-border-radius-base);
  border: none; /* 移除内容区自身的边框，由外部容器控制 */
  min-height: 150px; /* 确保内容区有最小高度 */
  font-size: 14px; /* 统一内容字体大小 */
  line-height: 1.6; /* 改善内容行高 */
  color: var(--el-text-color-primary);
  background-color: #fff; /* 内容区背景色 */
}

/* 解决文字堆叠问题，通常是行高或字体问题 */
.quill-editor-container :deep(.ql-editor) {
  padding: 12px 15px; /* 内容区的内边距 */
  line-height: 1.7; /* 明确设置编辑区域的行高 */
  overflow-y: auto; /* 如果内容过多，允许滚动 */
  /* 尝试重置可能影响的字体 */
  /* font-family: var(--el-font-family); */ /* 如果 Element Plus 有定义全局字体 */
}

/* 如果工具栏图标过小或显示不正确，可以尝试调整 */
.quill-editor-container :deep(.ql-snow .ql-picker-label) {
  font-size: 13px; /* 调整下拉选择器的字体大小 */
}

.quill-editor-container :deep(.ql-snow.ql-toolbar button svg),
.quill-editor-container :deep(.ql-snow .ql-toolbar button svg) {
  width: 16px; /* 调整图标大小 */
  height: 16px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .grade-page-container {
    padding: 15px;
  }

  .submission-column, .grading-column {
    width: 100%; /* 小屏幕时，左右两栏都占满宽度 */
  }

  .page-header .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header .header-content .el-tag {
    margin-left: 0;
    margin-top: 8px;
  }
}
</style>