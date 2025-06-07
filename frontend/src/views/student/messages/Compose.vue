<template>
  <div>
    <h2>写新消息</h2>
    <el-form :model="form" label-width="80px">
      <el-form-item label="收件人">
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
              :label="`${item.name} (${item.username})`"
              :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="主题">
        <el-input v-model="form.title"/>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="10"/>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSend" :loading="sending">发送</el-button>
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
  content: ''
})
const searchLoading = ref(false)
const sending = ref(false)
const userOptions = ref([])

const searchUsersRemote = async (query) => {
  if (query) {
    searchLoading.value = true
    try {
      const response = await searchUsers(query)
      userOptions.value = response.data
    } finally {
      searchLoading.value = false
    }
  } else {
    userOptions.value = []
  }
}

const handleSend = async () => {
  if (!form.value.recipient || !form.value.title.trim() || !form.value.content.trim()) {
    ElMessage.warning('收件人、主题和内容均不能为空')
    return
  }
  sending.value = true
  try {
    await sendMessage(form.value)
    ElMessage.success('发送成功')
    router.push({name: 'StudentMessageInbox'})
  } finally {
    sending.value = false
  }
}
</script>