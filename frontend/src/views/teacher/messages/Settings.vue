<template>
  <div>
    <h2>消息设置</h2>
    <el-card v-loading="loading">
      <template #header>
        <span>接收规则</span>
      </template>
      <el-form label-position="top">
        <el-form-item label="私信接收策略">
          <el-radio-group v-model="settings.private_message_policy">
            <el-radio label="everyone">任何人</el-radio>
            <el-radio label="staff_only">仅限管理员</el-radio>
            <el-radio label="none">不接收任何人私信 (超级管理员除外)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider/>

        <el-form-item label="系统通知">
          <el-switch v-model="settings.receive_assignment_notifications" active-text="接收学生提交通知"/>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存设置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>黑名单管理</span>
      </template>
      <el-table :data="blockedContacts" v-loading="loadingBlocked">
        <el-table-column prop="blocked_user_details.name" label="用户名"/>
        <el-table-column prop="blocked_user_details.username" label="登录名"/>
        <el-table-column prop="timestamp" label="拉黑时间">
          <template #default="scope">{{ formatTime(scope.row.timestamp) }}</template>
        </el-table-column>
        <el-table-column label="操作">
          <template #default="scope">
            <el-button type="warning" size="small" @click="handleUnblock(scope.row.id)">解除屏蔽</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import {
  fetchNotificationSettings,
  updateNotificationSettings,
  fetchBlockedContacts,
  unblockContact
} from '@/api/notifications'
import {ElMessage} from 'element-plus'
import dayjs from 'dayjs'

const loading = ref(false)
const saving = ref(false)
const loadingBlocked = ref(false)
const settings = ref({})
const blockedContacts = ref([])

const loadSettings = async () => {
  loading.value = true
  try {
    const response = await fetchNotificationSettings()
    settings.value = response.data
  } finally {
    loading.value = false
  }
}

const loadBlockedContacts = async () => {
  loadingBlocked.value = true
  try {
    const response = await fetchBlockedContacts()
    blockedContacts.value = response.data
  } finally {
    loadingBlocked.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await updateNotificationSettings(settings.value)
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

const handleUnblock = async (id) => {
  await unblockContact(id)
  ElMessage.success('已解除屏蔽')
  loadBlockedContacts()
}

const formatTime = (time) => dayjs(time).format('YYYY-MM-DD HH:mm')

onMounted(() => {
  loadSettings()
  loadBlockedContacts()
})
</script>