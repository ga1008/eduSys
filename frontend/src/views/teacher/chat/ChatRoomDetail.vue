<template>
  <div class="chat-detail-container">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="text-large font-600 mr-3">{{ roomName }}</span>
      </template>
    </el-page-header>

    <el-card class="chat-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="实时聊天" name="chat">
           <ChatRoom
             v-if="activeTab==='chat'"
             :room-id="id"
             @message-context-menu="handleMessageContextMenu"
            />
        </el-tab-pane>
        <el-tab-pane label="成员与管理" name="management">
           <ChatRoomManagement
             v-if="activeTab==='management'"
             :room-id="id"
           />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <div v-if="contextMenu.visible" :style="menuStyle" class="context-menu">
      <div class="menu-item" @click="handleDeleteMessage">
         <el-icon><Delete /></el-icon> 删除消息
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessageBox, ElMessage } from 'element-plus';
import { Delete } from '@element-plus/icons-vue';
import ChatRoom from '@/components/ChatRoom.vue'; // 复用聊天组件
import ChatRoomManagement from '@/components/ChatRoomManagement.vue'; // 管理面板组件
import { deleteMessageByAdmin } from '@/api/chatroom';

const props = defineProps({
  id: { // 从路由接收 room id
    type: String,
    required: true
  }
});

const router = useRouter();
const route = useRoute();
const roomName = ref(route.query.name || '在线研讨'); // 从query获取房间名，或默认
const activeTab = ref('chat');

const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  selectedMessage: null,
});

const menuStyle = computed(() => ({
  top: `${contextMenu.value.y}px`,
  left: `${contextMenu.value.x}px`,
}));

const goBack = () => {
  router.back();
};

const handleMessageContextMenu = ({ event, message }) => {
  event.preventDefault();
  contextMenu.value.visible = true;
  contextMenu.value.x = event.clientX;
  contextMenu.value.y = event.clientY;
  contextMenu.value.selectedMessage = message;
};

const closeContextMenu = () => {
  contextMenu.value.visible = false;
  contextMenu.value.selectedMessage = null;
};

const handleDeleteMessage = async () => {
  const message = contextMenu.value.selectedMessage;
  if (!message) return;

  closeContextMenu();

  await ElMessageBox.confirm('确定要删除这条消息吗？此操作不可恢复。', '警告', {
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    type: 'warning',
  });

  try {
    await deleteMessageByAdmin(props.id, message.id);
    ElMessage.success('消息已删除');
    // 注意：后端需要通过WebSocket广播消息删除事件，前端监听并移除该消息
    // 这里暂时不做前端的主动移除，等待后端广播
  } catch (error) {
    ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message));
  }
};

onMounted(() => {
  document.addEventListener('click', closeContextMenu);
});

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu);
});
</script>

<style scoped>
.chat-detail-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
  z-index: 3000;
  padding: 5px 0;
}
.menu-item {
  list-style: none;
  padding: 8px 15px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
}
.menu-item .el-icon {
  margin-right: 8px;
}
.menu-item:hover {
  background-color: #ecf5ff;
  color: #409eff;
}
</style>