<template>
  <div class="grade-container">
    <el-page-header :content="sub.title || '作业批改'" @back="$router.back()" />

    <!-- 学生提交内容 -->
    <el-card class="submission-card">
      <template #header>
        <div class="student-header">
          <span class="student-name">{{ sub.student_name }}（{{ sub.student_number }}）</span>
          <span class="submit-time">提交于
            <el-tag type="success" size="small">
              {{ dayjs(sub.submit_time).format('YYYY-MM-DD HH:mm') }}
            </el-tag>
          </span>
        </div>
      </template>

      <div v-if="safeContent" v-html="safeContent" class="markdown-content" />
      <el-empty v-else description="学生未提交任何文本内容" :image-size="80" class="markdown-content-empty"/>

      <!-- 图片附件缩略图 -->
      <div v-if="imageFiles.length" class="image-thumbnails">
        <el-image
          v-for="(img, index) in imageFiles"
          :key="img.id || img.url"
          :src="img.url"
          :preview-src-list="imageFiles.map(f => f.url)"
          :initial-index="index"
          fit="cover"
          class="thumbnail"
          lazy
          preview-teleported
        />
      </div>

      <!-- 其他附件 -->
      <div v-if="otherFiles.length" class="file-list">
        <el-link
          v-for="f in otherFiles"
          :key="f.id || f.url"
          :href="f.url"
          target="_blank"
          type="primary"
          class="file-item"
        >
          <el-icon><Download /></el-icon>
          {{ f.original_name }}
        </el-link>
      </div>

      <el-empty v-if="!imageFiles.length && !otherFiles.length && !safeContent" description="学生未提交任何内容" :image-size="100" />

    </el-card>

    <!-- 批改表单 -->
    <el-card class="grade-form-card">
      <el-form label-width="90px">
        <el-form-item label="分数">
          <el-input-number v-model="score" :min="0" :max="sub.max_score || 100" />
          <span class="max-score">/ {{ sub.max_score || 100 }}</span>
        </el-form-item>

        <el-form-item label="评语">
          <el-input
            v-model="comment"
            type="textarea"
            :rows="4"
            placeholder="写点鼓励或建议吧…"
          />
        </el-form-item>

        <el-form-item label="退回重做">
          <el-switch v-model="isReturned" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { gradeSubmission } from '@/api/homeworks'
import couRequest from '@/utils/request_cou'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const subId = route.params.subId

const sub = ref({
  title: '',
  content: '',
  files: [],
  student_name: '',
  student_number: '',
  submit_time: '',
  max_score: 100,
  student: {}
})
const score = ref(null)
const comment = ref('')
const isReturned = ref(false)
const saving = ref(false)

const imageFiles = computed(() =>
  sub.value.files.filter(f => f && f.original_name && /\.(jpg|jpeg|png|gif)$/i.test(f.original_name))
)
const otherFiles = computed(() =>
  sub.value.files.filter(f => f && f.original_name && !/\.(jpg|jpeg|png|gif)$/i.test(f.original_name))
)

const safeContent = computed(() => {
  // 简单处理，实际项目中可能需要更完善的XSS防护库如DOMPurify
  return sub.value.content || ''
})

onMounted(async () => {
  try {
    const { data } = await couRequest.get(`/homeworks/submissions/${subId}/`)
    sub.value = data
    score.value = data.score ?? null
    comment.value = data.teacher_comment || ''
    isReturned.value = data.is_returned || false
    // 确保 student 对象存在
    sub.value.student_name = data.student?.name || '未知学生'
    sub.value.student_number = data.student?.student_number || 'N/A'
    sub.value.max_score = data.homework?.max_score || 100 // 从作业信息获取满分
    sub.value.title = data.homework?.title || '作业详情'
  } catch (error) {
    console.error('获取作业提交失败:', error)
    ElMessage.error('获取作业数据失败，请稍后重试')
    // 可以选择返回上一页或显示错误信息
    // router.back()
  }
})

const submit = async () => {
  saving.value = true

  // 如果退回重做，则分数为 null，否则使用输入的分数
  const finalScore = isReturned.value ? null : (score.value !== null ? score.value : sub.value.max_score || 100)
  try {
    await gradeSubmission(subId, {
      score: finalScore,
      teacher_comment: comment.value || '已阅', // 如果评语为空，默认为'已阅'
      is_returned: isReturned.value
    })
    ElMessage.success('批改保存成功')
    router.back()
  } catch (error) {
    console.error('保存批改失败:', error)
    let errMsg = '保存批改失败'
    if (error.response && error.response.data && error.response.data.detail) {
        if (typeof error.response.data.detail === 'string') {
            errMsg = error.response.data.detail
        } else if (Array.isArray(error.response.data.detail) && error.response.data.detail.length > 0 && error.response.data.detail[0].msg) {
            errMsg = error.response.data.detail[0].msg
        }
    } else if (error.message) {
        errMsg = error.message
    }
    ElMessage.error(errMsg)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.grade-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.submission-card {
  margin-top: 20px;
  margin-bottom: 24px;
}

.student-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-name {
  font-weight: bold;
  font-size: 1.1em;
}

.submit-time {
  font-size: 0.9em;
  color: #606266;
}

.markdown-content {
  margin-top: 16px;
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fdfdfd;
  line-height: 1.75;
  word-wrap: break-word;
}

.markdown-content-empty {
  margin-top: 16px;
  margin-bottom: 20px;
}


.image-thumbnails {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
  margin-bottom: 20px;
}

.thumbnail {
  width: 100px;
  height: 100px;
  border-radius: 6px;
  cursor: pointer;
  object-fit: cover;
  border: 1px solid #e0e0e0;
  transition: transform 0.2s ease-in-out;
}
.thumbnail:hover {
  transform: scale(1.05);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
  margin-bottom: 10px; /* Adjusted margin if it's the last element in card */
}

.file-item {
  display: inline-flex; /* Changed to inline-flex for better alignment */
  align-items: center;
  gap: 6px;
  padding: 4px 0;
}
.file-item .el-icon {
  font-size: 1.1em;
}

.grade-form-card {
  margin-top: 20px;
}

.max-score {
  margin-left: 10px;
  color: #909399;
  font-size: 0.9em;
}

/* Ensure el-empty is centered if it's the only thing in the card */
.submission-card .el-empty {
  padding: 20px 0;
}
</style>