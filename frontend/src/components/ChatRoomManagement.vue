<template>
  <div class="management-panel" v-loading="loading">
    <el-divider content-position="left">房间设置</el-divider>
    <div class="setting-item">
      <span>全员禁言</span>
      <el-switch v-model="roomSettings.is_muted" @change="handleMuteToggle"/>
    </div>

    <el-divider content-position="left">成员列表 ({{ members.length }})</el-divider>
    <el-table :data="members" stripe style="width: 100%">
      <el-table-column label="昵称" prop="nickname">
        <template #default="scope">
          <span>{{ scope.row.nickname }}</span>
          <el-button link type="primary" :icon="Edit" @click="changeNickname(scope.row)"/>
        </template>
      </el-table-column>
      <el-table-column label="用户" prop="user_info.name">
        <template #default="scope">
          {{ scope.row.user_info.name || scope.row.user_info.username }}
        </template>
      </el-table-column>
      <el-table-column label="角色" prop="role">
        <template #default="scope">
          <el-tag :type="scope.row.role === 'admin' ? 'success' : 'info'" size="small">
            {{ scope.row.role === 'admin' ? '管理员' : '成员' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作">
        <template #default="scope">
          <el-button
              link
              type="primary"
              @click="toggleAdmin(scope.row)"
              :disabled="scope.row.user_info.role === 'teacher'"
          >
            {{ scope.row.role === 'admin' ? '取消管理' : '设为管理' }}
          </el-button>
          <el-button
              link
              type="danger"
              @click="kickUser(scope.row)"
              :disabled="scope.row.user_info.role !== 'student'"
          >
            移出群聊
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';
import {ElMessage, ElMessageBox} from 'element-plus';
import {Edit} from '@element-plus/icons-vue';
import {
  fetchChatMembers,
  updateRoomSettings,
  setMemberRole,
  kickMember,
  updateMemberNicknameByAdmin
} from '@/api/chatroom';

const props = defineProps({
  roomId: {
    type: [String, Number],
    required: true
  }
});

const loading = ref(true);
const members = ref([]);
const roomSettings = ref({
  is_muted: false,
});

const loadMembers = async () => {
  loading.value = true;
  try {
    const response = await fetchChatMembers(props.roomId);
    members.value = response.data;
  } catch (error) {
    ElMessage.error('加载成员列表失败');
  } finally {
    loading.value = false;
  }
};

const handleMuteToggle = async (value) => {
  try {
    await updateRoomSettings(props.roomId, {is_muted: value});
    ElMessage.success(`已${value ? '开启' : '关闭'}全员禁言`);
  } catch (error) {
    ElMessage.error('操作失败');
    roomSettings.value.is_muted = !value; // 恢复原状
  }
};

const changeNickname = async (member) => {
  const {value} = await ElMessageBox.prompt('请输入新的昵称', '修改昵称', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: member.nickname,
  });

  if (value && value !== member.nickname) {
    try {
      // 假设有此API
      await updateMemberNicknameByAdmin(props.roomId, member.id, value);
      member.nickname = value;
      ElMessage.success('昵称修改成功');
    } catch (error) {
      ElMessage.error('修改失败: ' + (error.response?.data?.detail || error.message));
    }
  }
};

const toggleAdmin = async (member) => {
  const newRole = member.role === 'admin' ? 'member' : 'admin';
  const actionText = newRole === 'admin' ? '设为' : '取消';
  await ElMessageBox.confirm(`确定要${actionText}管理员吗？`, '确认', {type: 'warning'});

  try {
    await setMemberRole(props.roomId, member.id, newRole);
    member.role = newRole;
    ElMessage.success('操作成功');
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message));
  }
};

const kickUser = async (member) => {
  await ElMessageBox.confirm(`确定要将“${member.nickname}”移出群聊吗？`, '警告', {type: 'danger'});
  try {
    await kickMember(props.roomId, member.id);
    ElMessage.success('已将该成员移出');
    loadMembers(); // 重新加载成员列表
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message));
  }
};

onMounted(loadMembers);
</script>

<style scoped>
.management-panel {
  padding: 10px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
}
</style>