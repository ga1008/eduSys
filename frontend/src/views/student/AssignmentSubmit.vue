<template>
  <div class="p-6 space-y-6">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="提交 / 编辑" name="edit">
        <!-- ↓ 原有编辑卡片全部放这里 ↓ -->
      <div class="assignment-container p-6">
    <!-- 加载中骨架 -->
    <el-skeleton v-if="loading" animated :rows="6" />

    <!-- 加载失败 -->
    <el-alert
      v-else-if="loadError"
      type="error"
      :closable="false"
      :title="loadError"
      show-icon
    />

    <template v-else>
      <!-- 顶部导航 -->
      <div class="mb-6 flex items-center justify-between">
        <el-button
          @click="$router.push('/student/assignments')"
          plain
          icon="el-icon-arrow-left">
          返回作业列表
        </el-button>
        <el-tag
          size="large"
          :type="isOverdue ? 'danger' : 'success'">
          {{ isOverdue ? '已截止' : '进行中' }}
        </el-tag>
      </div>

      <!-- 作业详情卡片 -->
  <el-card class="mb-6" shadow="hover">
    <div class="assignment-header">
      <h1 class="text-xl font-bold mb-2">{{ assignment.title }}</h1>
      <div class="text-gray-600 mb-4">《{{ assignment.course_class_name }}》</div>
    </div>

    <el-divider />

    <!-- 改为卡片布局 -->
      <div class="info-cards">
        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <el-icon class="info-icon"><Clock /></el-icon>
            <div class="info-title">截止</div>
            <div :class="{'text-danger': isOverdue}" class="info-value">
              {{ formatDateTime(assignment.due_date) }}
            </div>
            <el-tag v-if="!isOverdue" size="small" type="warning" class="mt-2">
              剩余 {{ remainingTime }}
            </el-tag>
          </div>
        </el-card>

        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <el-icon class="info-icon"><Trophy /></el-icon>
            <div class="info-title">满分</div>
            <div class="info-value">{{ assignment.max_score }} 分</div>
          </div>
        </el-card>

        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <el-icon class="info-icon"><Calendar /></el-icon>
            <div class="info-title">时间</div>
            <div class="info-value">{{ formatDateTime(assignment.deploy_date) }}</div>
          </div>
        </el-card>

        <el-card class="info-card" shadow="hover">
          <div class="info-card-content">
            <el-icon class="info-icon"><User /></el-icon>
            <div class="info-title">发布</div>
            <div class="info-value">{{ assignment.deployer_name }}</div>
          </div>
        </el-card>
      </div>

      <!-- 作业说明 -->
      <div class="mt-6">
        <div class="font-medium text-lg mb-2 flex items-center">
          <el-icon class="mr-2"><Document /></el-icon>作业要求
        </div>
        <div class="description-box p-4 bg-gray-50 rounded-md markdown-content" v-html="formattedDescription"></div>
      </div>
    </el-card>

      <!-- 已提交状态卡片 -->
      <template v-if="submitted">
        <el-card class="mb-6" shadow="hover">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <el-icon color="#67C23A" class="mr-2"><CircleCheckFilled /></el-icon>
                <span class="font-bold">提交状态</span>
              </div>
              <el-button
                type="primary"
                plain
                size="small"
                @click="submitted = false">
                重新提交
              </el-button>
            </div>
          </template>

          <div class="submission-info p-4">
            <p><span class="font-medium">提交时间:</span> {{ formatDateTime(mySubmission?.submit_time || new Date()) }}</p>
            <p v-if="mySubmission?.score">
              <span class="font-medium">得分:</span>
              <span :class="scoreClass">{{ mySubmission.score }}</span>
            </p>

            <div class="files-list mt-4" v-if="mySubmission?.files?.length">
              <p class="font-medium mb-2">已提交文件:</p>
              <div
                v-for="file in mySubmission.files"
                :key="file.id"
                class="file-item">
                <el-icon><Document /></el-icon>
                <span>{{ file.name }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </template>

      <!-- 提交表单 -->
      <el-card v-else shadow="hover">
        <template #header>
          <div class="font-bold">
            <el-icon class="mr-2"><Upload /></el-icon>
            提交作业
          </div>
        </template>

        <el-form ref="formRef" :model="form" label-width="100px">
          <el-form-item label="作业附件" required>
            <el-upload
              v-model:file-list="form.files"
              :auto-upload="false"
              :limit="3"
              drag
              :on-exceed="handleExceed"
              :on-change="handleFileChange"
              multiple
            >
              <el-icon class="el-icon--upload"><Upload /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或 <em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip text-gray-500">
                  * 最多可上传3个文件，总大小不超过50MB
                </div>
              </template>
            </el-upload>
          </el-form-item>

          <el-form-item label="备注说明" v-if="!isOverdue">
            <!-- 使用富文本编辑器替换原来的textarea -->
            <div class="quill-editor">
              <QuillEditor
                v-model:content="form.comment"
                contentType="html"
                theme="snow"
                :toolbar="editorToolbar"
                placeholder="可以在这里添加对作业的说明（选填）"
              />
            </div>
          </el-form-item>

          <el-form-item style="padding-top: 20px">
            <el-button
              type="primary"
              @click="handleSubmit"
              :loading="submitting"
              :disabled="isOverdue || !form.files.length">
              {{ isOverdue ? '已截止，无法提交' : '提交作业' }}
            </el-button>
            <el-button @click="$router.push('/student/assignments')">取消</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>
  </div>
      </el-tab-pane>

      <el-tab-pane label="历史记录" name="history">
        <submission-history-tab
          :submissions="assignment.submissions"
          @load="loadHistory"
          @delete="handleDelete"
        />
      </el-tab-pane>
    </el-tabs>
   </div>

</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

import 'dayjs/locale/zh-cn'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Clock, Trophy, User, Document, Upload, CircleCheckFilled } from '@element-plus/icons-vue'
import {deleteDrawSubmission, fetchAssignmentInfo, fetchMySubmission, submitAssignmentWithFiles} from '@/api/student.js'

// 引入 Quill 编辑器
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import hljs from 'markdown-it-highlightjs'
import 'highlight.js/styles/github.css' // 选择一个代码高亮主题
import SubmissionHistoryTab from '@/views/student/SubmissionHistoryTab.vue'
import stuRequest from '@/utils/request_stu'

// 配置 dayjs
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const props = defineProps({ id: { type: [String, Number], required: true } })
const router = useRouter()

/* ------------ state ------------ */
const activeTab = ref('edit')
const loading = ref(true)
const loadError = ref('')
const assignment = ref({})
const submitted = ref(false)
const mySubmission = ref(null)
const formRef = ref()
const form = ref({
  files: [],
  comment: ''
})
const submitting = ref(false)

/* ------------ computed ------------ */
const isOverdue = computed(() => {
  if (!assignment.value?.due_date) return false
  return dayjs(assignment.value.due_date).isBefore(dayjs())
})

// 创建并配置markdown-it实例
const md = new MarkdownIt({
  html: true,        // 启用HTML标签
  breaks: true,      // 将换行符转换为<br>
  linkify: true,     // 自动转换URL为链接
  typographer: true, // 启用一些语言中立的替换和引号
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {}
    }
    return ''; // 使用默认的转义
  }
})

const formattedDescription = computed(() => {
  if (!assignment.value?.description) return ''
  const renderedHTML = md.render(assignment.value.description)
  return DOMPurify.sanitize(renderedHTML)
})

// 富文本编辑器工具栏配置
const editorToolbar = [
  ['bold', 'italic', 'underline', 'strike'],
  ['blockquote', 'code-block'],
  [{ 'header': 1 }, { 'header': 2 }],
  [{ 'list': 'ordered' }, { 'list': 'bullet' }],
  [{ 'color': [] }, { 'background': [] }],
  ['link', 'image'],
  ['clean']
]

const remainingTime = computed(() => {
  if (!assignment.value?.due_date) return ''
  const now = dayjs()
  const due = dayjs(assignment.value.due_date)

  if (due.isBefore(now)) return '已截止'

  const diffDays = due.diff(now, 'day')
  const diffHours = due.diff(now, 'hour') % 24
  const diffMinutes = due.diff(now, 'minute') % 60

  if (diffDays > 0) {
    return `${diffDays}天 ${diffHours}小时`
  }
  if (diffHours > 0) {
    return `${diffHours}小时 ${diffMinutes}分钟`
  }
  return `${diffMinutes}分钟`
})

const scoreClass = computed(() => {
  if (!mySubmission.value?.score) return ''
  const score = parseFloat(mySubmission.value.score)
  const max = parseFloat(assignment.value.max_score || 100)

  if (score >= max * 0.8) return 'text-success'
  if (score >= max * 0.6) return 'text-warning'
  return 'text-danger'
})

/* ------------ methods ------------ */
const formatDateTime = (dateString) => {
  if (!dateString) return '未知'
  return dayjs(dateString).format('YYYY-MM-DD HH:mm')
}

const handleFileChange = (file) => {
  // 文件大小检查
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.warning('文件大小不能超过50MB')
    return false
  }
  return true
}

const handleExceed = () => {
  ElMessage.warning('最多只能上传3个文件')
}

 /* ========== 载入历史记录到表单 ========== */
 const loadHistory = (row) => {
   form.value.title   = row.title || assignment.title
   form.value.content = row.content || ''
   // 由于后端不返回文件二进制，这里仅提示用户需重新选择文件
   ElMessage.info('已载入文字内容，请重新选择附件后提交')
   submitted.value = false
   activeTab.value = 'edit'
 }

 /* ========== 撤回 / 删除历史提交 ========== */
const handleDelete = async (row) => {
  try {
    await deleteDrawSubmission(row.submit_id)   // 调后端 DELETE
    ElMessage.success('已撤回，可重新提交')

  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '撤回失败')
  } finally {
    // 刷新当前作业信息
    await fetchAssignmentInfo(props.id)
    // 重新载入我的提交
    const res = await fetchMySubmission(props.id)
    mySubmission.value = res.data
    submitted.value = true
  }
}

const handleSubmit = async () => {

   // 检查 comment 大小，大于10mb不允许提交
  const maxCommentSize = 10 * 1024 * 1024 // 10MB
  if (form.value.comment && form.value.comment.length > maxCommentSize) {
    ElMessage.warning('备注说明不能超过10MB')
    return
  }

  if (!form.value.files.length) {
    ElMessage.warning('请至少选择一个文件提交')
    return
  }

  if (isOverdue.value) {
    ElMessage.error('该作业已截止，无法提交，请向老师申请延期')
    return
  }

  // 确认提交
  try {
    await ElMessageBox.confirm(
      '确认提交吗？',
      '提交确认',
      {
        confirmButtonText: '确认提交',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  } catch {
    return // 用户取消提交
  }

  const fd = new FormData()
  fd.append("assignmentId", props.id)
  fd.append('title', assignment.value.title)
  fd.append('content', form.value.comment || '')
  form.value.files.forEach(f => fd.append('files', f.raw))

  submitting.value = true
  try {
    if (submitted.value) {
       // 覆盖更新
       fd.append('_method', 'PATCH')            // Laravel 风格；若不需要可改用 stuRequest.patch
       await stuRequest.patch(`/assignments/submissions/${mySubmission.value.id}/`, fd)
     } else {
       await submitAssignmentWithFiles(props.id, fd)
     }
    ElMessage.success('提交成功')

  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败，请稍后重试')
  } finally {
    // 更新状态
    submitting.value = false
    submitted.value = true
    // 重新加载作业信息
    const res = await fetchAssignmentInfo(props.id)
    assignment.value = res.data
  }
}

/* ------------ init ------------ */
onMounted(async () => {
  try {
    loading.value = true
    // 并行请求
    const [infoRes, subRes] = await Promise.allSettled([
      fetchAssignmentInfo(props.id),
      fetchMySubmission(props.id)
    ])

    // 作业信息必须成功
    if (infoRes.status === 'fulfilled') {
      assignment.value = infoRes.value.data
      document.title = `${assignment.value.title} - 作业提交`

      if (assignment.value.submissions) {
        mySubmission.value = assignment.value.submissions.find(sub => sub.student_id === assignment.value.student_id)
      } else {
        mySubmission.value = null
      }
      submitted.value = !!assignment.value.submitted;
    } else {
      throw new Error('无法获取作业信息')
    }

    // 我的提交：可能 404
    if (subRes.status === 'fulfilled') {
      mySubmission.value = subRes.value.data
    } else {
      // 其它错误
      throw new Error('加载提交记录失败')
    }
  } catch (err) {
    loadError.value = err.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.assignment-container {
  max-width: 900px;
  margin: 0 auto;
}

.assignment-header {
  text-align: center;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.description-box {
  line-height: 1.6;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 4px;
  background-color: #f5f7fa;
  margin-bottom: 8px;
}

.info-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.info-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.info-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.info-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  text-align: center;
}

.info-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}

.info-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.info-value {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 6px;
}

/* 富文本编辑器样式 */
.quill-editor {
  height: 200px;
  margin-bottom: 20px;
}

:deep(.ql-container) {
  font-size: 14px;
}

:deep(.ql-editor) {
  min-height: 150px;
}

.text-success {
  color: #67C23A;
}

.text-warning {
  color: #E6A23C;
}

.text-danger {
  color: #F56C6C;
}

:deep(.el-upload-dragger) {
  width: 100%;
}

/* Markdown内容样式 */
.markdown-content :deep(h1) {
  font-size: 2em;
  margin-top: 0.67em;
  margin-bottom: 0.67em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  margin-top: 0.83em;
  margin-bottom: 0.83em;
}

.markdown-content :deep(h3) {
  font-size: 1.17em;
  margin-top: 1em;
  margin-bottom: 1em;
}

.markdown-content :deep(h4) {
  margin-top: 1.33em;
  margin-bottom: 1.33em;
}

.markdown-content :deep(h5) {
  font-size: 0.83em;
  margin-top: 1.67em;
  margin-bottom: 1.67em;
}

.markdown-content :deep(h6) {
  font-size: 0.67em;
  margin-top: 2.33em;
  margin-bottom: 2.33em;
}

.markdown-content :deep(p) {
  margin-top: 1em;
  margin-bottom: 1em;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 2em;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
  margin-top: 1em;
  margin-bottom: 1em;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin-bottom: 0.5em;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #ccc;
  margin-left: 0;
  padding-left: 1em;
  color: #666;
}

.markdown-content :deep(code:not(.hljs)) {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 3px;
}

.markdown-content :deep(pre) {
  padding: 1em;
  overflow: auto;
  border-radius: 5px;
  margin: 1em 0;
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f2f2f2;
}

.markdown-content :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
}
</style>