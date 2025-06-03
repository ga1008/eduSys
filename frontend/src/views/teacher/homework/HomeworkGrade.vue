<template>
  <div class="grade-container p-6 bg-gray-50 min-h-screen">
    <el-page-header @back="$router.back()" class="mb-6">
      <template #content>
        <span class="text-lg font-semibold">批改作业：{{ submissionData.homework?.title || '加载中...' }}</span>
      </template>
    </el-page-header>

    <el-row :gutter="24">
      <el-col :xs="24" :sm="24" :md="12">
        <el-card class="submission-card student-submission-panel" shadow="hover">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-lg font-bold text-gray-700">学生提交详情</span>
              <el-tag effect="light" size="small">
                {{ submissionData.student?.name || '未知学生' }} ({{ submissionData.student?.student_number || 'N/A' }})
              </el-tag>
            </div>
          </template>
          <div v-if="loadingSubmission" class="p-4">
            <el-skeleton :rows="5" animated />
          </div>
          <div v-else>
            <div class="submission-meta p-4 border-b border-gray-200">
               <p><strong>提交标题:</strong> {{ submissionData.title || '(学生未填写标题)' }}</p>
               <p><strong>提交时间:</strong>
                <el-tag type="info" effect="plain" size="small">
                  {{ dayjs(submissionData.submit_time).format('YYYY-MM-DD HH:mm:ss') }}
                </el-tag>
              </p>
            </div>

            <div class="content-viewer p-4">
              <h4 class="text-sm font-semibold mb-2 text-gray-600">提交文本内容:</h4>
              <div v-if="submissionData.content" v-html="renderMarkdown(submissionData.content)" class="markdown-content-display p-3 border rounded-md bg-white min-h-[100px]"></div>
              <el-empty v-else description="学生未提交任何文本内容" :image-size="60" class="py-4"/>
            </div>

            <div v-if="submissionData.files && submissionData.files.length > 0" class="files-display p-4 border-t border-gray-200">
              <h4 class="text-sm font-semibold mb-3 text-gray-600">提交附件 ({{ submissionData.files.length }}):</h4>
              <div v-if="imageFiles.length" class="image-thumbnails mb-3">
                <el-image
                  v-for="(img, index) in imageFiles"
                  :key="img.id || img.name"
                  :src="img.url"
                  :preview-src-list="imageFiles.map(f => f.url)"
                  :initial-index="index"
                  fit="cover"
                  class="thumbnail"
                  lazy
                  preview-teleported
                />
              </div>
              <div v-if="otherFiles.length" class="file-list">
                <el-link
                  v-for="f in otherFiles"
                  :key="f.id || f.name"
                  :href="f.url"
                  target="_blank"
                  type="primary"
                  class="file-item"
                  :underline="false"
                >
                  <el-icon class="mr-1"><Paperclip /></el-icon>
                  {{ f.original_name || f.name }}
                </el-link>
              </div>
            </div>
            <el-empty v-if="(!submissionData.files || submissionData.files.length === 0) && !submissionData.content" description="学生未提交任何附件或文本" :image-size="80" class="py-4"/>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="12">
        <el-card v-if="submissionData.assignment?.ai_grading_enabled" class="ai-suggestions-card mb-6" shadow="hover">
          <template #header>
            <div class="flex justify-between items-center">
              <span class="text-lg font-bold text-gray-700">AI 辅助批改建议</span>
              <el-tag :type="aiStatusTagType" effect="light" size="small">{{ aiStatusText }}</el-tag>
            </div>
          </template>
          <div v-if="loadingSubmission" class="p-4">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else-if="submissionData.ai_grading_status === 'completed' && submissionData.ai_score !== null">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="AI 建议分数">
                <el-tag :type="getScoreTagType(submissionData.ai_score, submissionData.homework?.max_score)" size="medium" effect="dark">
                  {{ submissionData.ai_score }} / {{ submissionData.homework?.max_score || 100 }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="AI 建议评语" label-class-name="ai-comment-label">
                <div v-if="submissionData.ai_comment" v-html="renderMarkdown(submissionData.ai_comment)" class="markdown-content-display text-sm"></div>
                <span v-else class="text-gray-500 italic">AI未提供评语。</span>
              </el-descriptions-item>
              <el-descriptions-item label="AI 内容疑似度" v-if="typeof submissionData.ai_generated_similarity === 'number'">
                 <el-progress
                    :percentage="Math.round(submissionData.ai_generated_similarity * 100)"
                    :stroke-width="10"
                    :format="(percentage) => `${percentage}%`"
                    class="w-1/2"
                 />
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <div v-else-if="submissionData.ai_grading_status === 'failed' || submissionData.ai_grading_status === 'skipped'" class="p-4 text-center">
            <el-alert :title="`AI批改${submissionData.ai_grading_status === 'failed' ? '失败' : '跳过'}`" :description="submissionData.ai_comment || '无详细信息'" type="warning" show-icon :closable="false" />
          </div>
           <div v-else-if="submissionData.ai_grading_status === 'processing' || submissionData.ai_grading_status === 'pending'" class="p-4 text-center">
            <div class="flex items-center justify-center text-gray-600">
              <el-icon class="is-loading mr-2"><Loading /></el-icon>
              <span>AI批改处理中，请稍后...</span>
            </div>
          </div>
          <el-empty v-else description="AI辅助批改未启用或暂无建议" :image-size="60" />
        </el-card>

        <el-card class="grade-form-card teacher-grading-panel" shadow="hover">
          <template #header>
            <div class="text-lg font-bold text-gray-700">教师评分与评语</div>
          </template>
          <el-form :model="gradingForm" ref="gradingFormRef" label-position="top" class="p-1">
            <el-form-item label="最终分数" prop="score" :rules="scoreRules">
              <el-input-number v-model="gradingForm.score" :min="0" :max="submissionData.homework?.max_score || 100" controls-position="right" class="w-full"/>
              <span class="text-xs text-gray-500 ml-2">满分: {{ submissionData.homework?.max_score || 100 }}</span>
            </el-form-item>

            <el-form-item label="最终评语" prop="comment">
              <QuillEditor
                v-model:content="gradingForm.comment"
                contentType="html"
                theme="snow"
                placeholder="请输入您的最终评语..."
                style="min-height: 150px; width: 100%;"
                class="mb-2"
              />
            </el-form-item>

            <el-form-item label="退回重做" prop="isReturned">
              <el-switch
                v-model="gradingForm.isReturned"
                @change="handleReturnChange"
                active-text="是"
                inactive-text="否"
              />
              <el-tooltip content="开启后，本次评分将无效，学生需要重新提交。" placement="top">
                <el-icon class="ml-2 cursor-pointer text-gray-400"><QuestionFilled /></el-icon>
              </el-tooltip>
            </el-form-item>

            <el-form-item class="mt-6">
              <el-button type="primary" :loading="saving" @click="submitGrade" icon="el-icon-check" size="large">
                保存批改
              </el-button>
              <el-button @click="$router.back()" size="large">取消</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { gradeSubmission } from '@/api/homeworks' //
import couRequest from '@/utils/request_cou' //
import { ElMessage } from 'element-plus'
import { Download, Paperclip, Loading, QuestionFilled } from '@element-plus/icons-vue' // Replaced old icons
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const route = useRoute()
const router = useRouter()
const subId = route.params.subId // From route, e.g., /homeworks/submissions/:subId/grade

const loadingSubmission = ref(true)
const submissionData = ref({ // Stores all data related to the submission
  title: '', // Student's submission title
  content: '', // Student's text content
  files: [],
  student: { name: '', student_number: '' }, // student info
  homework: { title: '', max_score: 100 }, // related assignment info
  submit_time: '',
  score: null, // teacher's score
  teacher_comment: '', // teacher's comment
  is_returned: false,
  ai_score: null,
  ai_comment: '',
  ai_generated_similarity: null,
  ai_grading_status: null,
  assignment: null, // to store parent assignment details if needed like ai_grading_enabled
})

const gradingFormRef = ref(null)
const gradingForm = ref({
  score: null,
  comment: '',
  isReturned: false
})
const saving = ref(false)

const md = new MarkdownIt({ html: true, linkify: true, typographer: true });
const renderMarkdown = (text) => text ? DOMPurify.sanitize(md.render(text)) : '';

const imageFiles = computed(() =>
  submissionData.value.files?.filter(f => f && f.original_name && /\.(jpg|jpeg|png|gif|webp)$/i.test(f.original_name)) || []
)
const otherFiles = computed(() =>
  submissionData.value.files?.filter(f => f && f.original_name && !/\.(jpg|jpeg|png|gif|webp)$/i.test(f.original_name)) || []
)

const aiStatusText = computed(() => {
  switch (submissionData.value.ai_grading_status) {
    case 'completed': return 'AI建议已生成';
    case 'processing': return 'AI处理中';
    case 'pending': return '等待AI处理';
    case 'failed': return 'AI处理失败';
    case 'skipped': return 'AI已跳过';
    default: return '未启用或未知';
  }
});

const aiStatusTagType = computed(() => {
  switch (submissionData.value.ai_grading_status) {
    case 'completed': return 'success';
    case 'processing': return 'primary';
    case 'pending': return 'info';
    case 'failed': return 'danger';
    case 'skipped': return 'warning';
    default: return 'info';
  }
});

const getScoreTagType = (score, maxScore = 100) => {
  if (score === null || typeof score === 'undefined') return 'info';
  const numericScore = parseFloat(score);
  const numericMaxScore = parseFloat(maxScore);
  if (numericScore >= numericMaxScore * 0.85) return 'success';
  if (numericScore >= numericMaxScore * 0.6) return 'warning';
  return 'danger';
};

watch(() => gradingForm.value.isReturned, (newValue) => {
  if (newValue === true) {
    // gradingForm.value.score = null; // 退回时，教师评分置空
    ElMessage.info('已选择退回重做，本次评分将不保存，学生需要重新提交。');
  }
});
const handleReturnChange = (isReturned) => {
  if(isReturned){
    gradingForm.value.score = null;
  }
}


onMounted(async () => {
  loadingSubmission.value = true;
  try {
    // API GET /cou/api/homeworks/submissions/<pk>/
    // This endpoint should return the AssignmentSubmission object,
    // and ideally populate related homework (Assignment) and student (User) details.
    const { data } = await couRequest.get(`/homeworks/submissions/${subId}/`)
    submissionData.value = data;

    // Initialize teacher's grading form with existing manual grades, or leave blank
    // Do NOT prefill with AI grades. AI grades are for reference only.
    gradingForm.value.score = data.score ?? null; // Teacher's manual score
    gradingForm.value.comment = data.teacher_comment || ''; // Teacher's manual comment
    gradingForm.value.isReturned = data.is_returned || false;

  } catch (error) {
    console.error('获取作业提交详情失败:', error);
    ElMessage.error('获取作业数据失败，请稍后重试。');
    // router.back(); // Optionally navigate back on critical error
  } finally {
    loadingSubmission.value = false;
  }
});

const scoreRules = [
  {
    validator: (rule, value, callback) => {
      if (gradingForm.value.isReturned) { // 如果退回，分数可以为空
        callback();
        return;
      }
      if (value === null || typeof value === 'undefined' || value === '') {
        callback(new Error('请输入分数'));
      } else if (value < 0 || value > (submissionData.value.homework?.max_score || 100)) {
        callback(new Error(`分数必须在 0 到 ${submissionData.value.homework?.max_score || 100}之间`));
      } else {
        callback();
      }
    },
    trigger: ['blur', 'change']
  }
];


const submitGrade = async () => {
  gradingFormRef.value?.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请检查评分表单是否完整。');
      return;
    }

    saving.value = true;
    const payload = {
      score: gradingForm.value.isReturned ? null : gradingForm.value.score,
      teacher_comment: gradingForm.value.comment || (gradingForm.value.isReturned ? '作业已退回，请修改后重新提交。' : '已批改。'),
      is_returned: gradingForm.value.isReturned
    };

    try {
      // API PATCH /cou/api/homeworks/submissions/<pk>/grade/
      await gradeSubmission(subId, payload);
      ElMessage.success('批改结果保存成功！');
      router.back();
    } catch (error) {
      console.error('保存批改失败:', error);
      ElMessage.error('保存批改失败：' + (error.response?.data?.detail || error.message || '网络错误'));
    } finally {
      saving.value = false;
    }
  });
};
</script>

<style scoped>
.grade-container {
  max-width: 1200px; /* 稍宽一些以容纳双栏 */
  margin: 0 auto;
}
.el-page-header {
  background-color: #fff;
  padding: 16px 24px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.student-submission-panel, .ai-suggestions-card, .teacher-grading-panel {
  margin-bottom: 24px;
  border: 1px solid #e9e9eb;
  border-radius: 6px;
}
.student-submission-panel .el-card__header,
.ai-suggestions-card .el-card__header,
.teacher-grading-panel .el-card__header {
  background-color: #fafafa;
  border-bottom: 1px solid #e9e9eb;
  padding: 12px 20px; /* 统一头部内边距 */
}
.submission-meta p {
  margin-bottom: 8px;
  font-size: 14px;
  color: #555;
}
.submission-meta strong {
  color: #333;
  margin-right: 8px;
}
.content-viewer h4, .files-display h4 {
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}

.markdown-content-display {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  background-color: #fdfdfd; /* 轻微背景色区分 */
}
.markdown-content-display :deep(p) { margin-bottom: 0.6em; }
.markdown-content-display :deep(ul), .markdown-content-display :deep(ol) { padding-left: 20px; margin-bottom: 0.6em; }
.markdown-content-display :deep(code) {
  background-color: #eef0f3;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-size: 90%;
}
.markdown-content-display :deep(pre) {
  background-color: #2d2d2d; /* 深色代码块背景 */
  color: #f8f8f2; /* 亮色代码文本 */
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
}
.markdown-content-display :deep(pre code) {
  background-color: transparent;
  padding: 0;
}
.markdown-content-display :deep(blockquote) {
  border-left: 4px solid #b3c0d1;
  padding-left: 1em;
  color: #6a7587;
  margin-left: 0;
  margin-bottom: 0.6em;
}


.image-thumbnails {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.thumbnail {
  width: 80px;
  height: 80px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-item {
  padding: 6px 0;
  font-size: 14px;
}
.file-item .el-icon {
  vertical-align: middle;
}

.ai-suggestions-card .el-descriptions {
  font-size: 14px;
}
:deep(.ai-comment-label) {
  /* 确保AI评语标签能容纳更多文字或调整对齐 */
  min-width: 100px !important;
  vertical-align: top;
}
.el-form-item {
  margin-bottom: 20px; /* 统一表单项间距 */
}
.el-form-item .el-input-number, .el-form-item .el-switch {
  vertical-align: middle; /* 确保与标签对齐 */
}
.quill-editor-container .ql-toolbar { /* 与HomeworkForm一致 */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
.quill-editor-container .ql-container { /* 与HomeworkForm一致 */
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
}
</style>