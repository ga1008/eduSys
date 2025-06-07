<template>
  <div>
    <h2>消息设置</h2>
    <el-card v-loading="loading">
      <template #header><span>接收规则</span></template>
      <el-form v-if="settings" label-position="top">
        <el-form-item label="私信接收策略">
          <el-radio-group v-model="settings.private_message_policy">
            <el-radio label="everyone">任何人</el-radio>
            <el-radio label="teachers_staff_only">仅限教师和管理员</el-radio>
            <el-radio label="none">不接收任何人私信 (超级管理员除外)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-divider/>
        <el-form-item label="系统通知">
          <el-switch v-model="settings.receive_assignment_notifications" active-text="接收作业发布通知"/>
          <el-switch v-model="settings.receive_grading_notifications" active-text="接收作业批改通知"
                     style="margin-left: 20px;"/>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存设置</el-button>
        </el-form-item>
      </el-form>
      <el-alert v-else title="无法加载设置" type="error" show-icon :closable="false"/>
    </el-card>
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>黑名单管理</span>
          <div class="add-block-form">
            <el-select v-model="userToBlock" filterable remote reserve-keyword placeholder="搜索用户以添加到黑名单"
                       :remote-method="searchUsersForBlocking" :loading="searchLoading" clearable
                       style="width: 250px; margin-right: 10px;">
              <el-option v-for="item in userOptions" :key="item.id"
                         :label="`${item.name || item.username} (${item.username})`" :value="item.id"/>
            </el-select>
            <el-button type="danger" @click="handleAddBlock" :disabled="!userToBlock">添加到黑名单</el-button>
          </div>
        </div>
      </template>
      <el-table :data="blockedContacts" v-loading="loadingBlocked" style="width: 100%">
        <el-table-column prop="blocked_user_details.name" label="姓名"/>
        <el-table-column prop="blocked_user_details.username" label="登录名"/>
        <el-table-column prop="blocked_user_details.role" label="角色"/>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button type="warning" size="small" @click="handleUnblock(scope.row.id)">解除屏蔽</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {
  fetchNotificationSettings,
  updateNotificationSettings,
  fetchBlockedContacts,
  unblockContact,
  blockContact,
  searchUsers
} from '@/api/notifications';
import {ElMessage} from 'element-plus';

const loading = ref(false);
const saving = ref(false);
const loadingBlocked = ref(false);
const settings = ref(null);
const blockedContacts = ref([]);
const userToBlock = ref(null);
const searchLoading = ref(false);
const userOptions = ref([]);

// 所有 methods (loadSettings, handleSave, 等) 与教师端完全一致，因为后端API会处理权限
const loadSettings = async () => {
  loading.value = true;
  try {
    const response = await fetchNotificationSettings();
    settings.value = response.data;
  } finally {
    loading.value = false;
  }
};
const handleSave = async () => {
  saving.value = true;
  try {
    await updateNotificationSettings(settings.value);
    ElMessage.success('设置已保存');
  } finally {
    saving.value = false;
  }
};

const loadBlockedContacts = async () => {
  loadingBlocked.value = true;
  try {
    const response = await fetchBlockedContacts();
    blockedContacts.value = response.data;
  } finally {
    loadingBlocked.value = false;
  }
};
const handleUnblock = async (id) => {
  await unblockContact(id);
  ElMessage.success('已解除屏蔽');
  await loadBlockedContacts();
};

const searchUsersForBlocking = async (query) => {
  if (query) {
    searchLoading.value = true;
    try {
      const response = await searchUsers(query);
      userOptions.value = response.data;
    } finally {
      searchLoading.value = false;
    }
  } else {
    userOptions.value = [];
  }
};
const handleAddBlock = async () => {
  if (!userToBlock.value) return;
  try {
    await blockContact(userToBlock.value);
    ElMessage.success('添加成功！');
    userToBlock.value = null;
    userOptions.value = [];
    await loadBlockedContacts();
  } catch (error) {
    // 错误已由axios拦截器统一处理
  }
};


onMounted(() => {
  loadSettings();
  loadBlockedContacts();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.add-block-form {
  display: flex;
  align-items: center;
}
</style>