<!-- Compose.vue -->
<template>
  <div>
    <h2>写新消息</h2>
    <el-form :model="form" label-width="80px">
      <el-form-item label="收件人" prop="recipient">
        <el-select
            v-model="form.recipient"
            filterable
            remote
            reserve-keyword
            placeholder="输入用户名、姓名或邮箱搜索"
            :remote-method="searchUsersRemote"
            :loading="searchLoading"
            style="width: 100%;"
        >
          <el-option
              v-for="item in userOptions"
              :key="item.id"
              :label="item.name + ' (' + item.username + ')'"
              :value="item.username"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="主题" prop="title">
        <el-input v-model="form.title" placeholder="输入主题"/>
      </el-form-item>

      <el-form-item label="内容" prop="content">
        <!-- 原生 Markdown 文本框 -->
        <el-input
            type="textarea"
            v-model="form.content"
            placeholder="支持 Markdown 格式"
            :autosize="{ minRows: 8, maxRows: 15 }"
        />
      </el-form-item>

      <el-form-item>
        <el-button
            type="primary"
            :loading="sending"
            @click="handleSend"
        >
          发送
        </el-button>
        <el-button @click="router.back()">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'
import {searchUsers, sendMessage} from '@/api/notifications'
import {ElMessage} from 'element-plus'

const router = useRouter()

const form = ref({
  recipient: '',
  title: '',
  content: ''  // 直接存储 Markdown 文本
})
const userOptions = ref([])
const searchLoading = ref(false)
const sending = ref(false)

const searchUsersRemote = async (query) => {
  if (!query) return
  searchLoading.value = true
  try {
    const res = await searchUsers({q: query})
    userOptions.value = res.data
  } finally {
    searchLoading.value = false
  }
}

const handleSend = async () => {
  if (!form.value.recipient || !form.value.title.trim() || !form.value.content.trim()) {
    ElMessage.warning('收件人、主题和内容均不能为空')
    return
  }
  sending.value = true
  try {
    // 直接发送 Markdown 文本
    await sendMessage({
      recipient: form.value.recipient,
      title: form.value.title,
      content: form.value.content
    })
    ElMessage.success('发送成功')
    router.push({name: 'StudentMessageInbox'})
  } catch (err) {
    console.error(err)
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.custom-quill-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
}

/* 确保编辑器内容区域有最小高度 */
.custom-quill-editor :deep(.ql-container) {
  min-height: 250px; /* 调整编辑器内容区域的最小高度 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.custom-quill-editor :deep(.ql-editor) {
  flex-grow: 1;
  overflow-y: auto; /* 内容超出时可滚动 */
  height: 100%; /* 配合 ql-container 的 flex 布局 */
}

/* 可以根据需要调整工具栏的样式 */
.custom-quill-editor :deep(.ql-toolbar) {
  background-color: #f8f9fa;
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

/* 调整表单项的底部外边距，避免与编辑器靠太近 */
.el-form-item:last-child {
  margin-bottom: 0;
}
</style>