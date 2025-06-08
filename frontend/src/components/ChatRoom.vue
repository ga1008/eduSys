<template>
  <div class="chat-room-container" v-loading="loading" element-loading-text="正在进入聊天室...">
    <el-container class="chat-layout">
      <el-main class="message-area" ref="messageAreaRef">
        <div class="history-loader">
          <el-button v-if="hasMoreHistory && !historyLoading" @click="loadHistory" size="small" round>
            加载更早的消息
          </el-button>
          <span v-if="historyLoading">正在加载...</span>
        </div>
        <div v-for="msg in messages" :key="msg.id"
             class="message-item"
             :class="getMessageClass(msg)"
             @contextmenu.prevent="handleContextMenu($event, msg)"
        >
          <div class="author-info">
            <el-tag :type="getRoleTagType(msg.author.role)" size="small" effect="dark" round>
              {{ msg.author.role === 'admin' ? '管理员' : '成员' }}
            </el-tag>
            <span class="nickname">{{ msg.author.nickname }}</span>
            <span class="timestamp">{{ formatTimestamp(msg.timestamp) }}</span>
          </div>
          <div class="message-content-wrapper">
            <div v-if="msg.message_type === 'text'" class="message-content text" v-html="msg.content"></div>
            <div v-else-if="msg.message_type === 'image'" class="message-content image">
              <el-image
                  style="max-width: 200px; max-height: 200px; border-radius: 8px;"
                  :src="msg.thumbnail_path"
                  :preview-src-list="[msg.file_path]"
                  fit="contain"
                  hide-on-click-modal
                  preview-teleported
              />
            </div>
            <div v-else class="message-content file">
              <el-icon>
                <Folder/>
              </el-icon>
              <span>{{ msg.file_original_name }}</span>
              <el-link :href="msg.file_path" type="primary" target="_blank" :underline="false"
                       style="margin-left: 10px;">下载
              </el-link>
            </div>
          </div>
        </div>
      </el-main>

      <el-footer class="input-area" height="160px">
        <div class="toolbar">
          <el-upload
              :action="`/chat/api/chatrooms/${roomId}/upload/`"
              :show-file-list="false"
              :before-upload="handleBeforeUpload"
              :http-request="handleCustomUpload"
              name="file"
          >
            <el-button :icon="Picture" circle title="发送图片/视频"></el-button>
          </el-upload>
          <el-upload
              :action="`/chat/api/chatrooms/${roomId}/upload/`"
              :show-file-list="false"
              :http-request="handleCustomUpload"
              :before-upload="handleBeforeUpload"
              name="file"
          >
            <el-button :icon="Folder" circle title="发送文件"></el-button>
          </el-upload>
        </div>
        <el-input
            v-model="newMessage"
            type="textarea"
            :rows="4"
            placeholder="输入消息内容，Shift + Enter 换行"
            resize="none"
            @keydown.enter.prevent="handleEnter"
        ></el-input>
        <el-button type="primary" @click="sendMessage" class="send-button">发送</el-button>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, nextTick} from 'vue';
import {useUserStore} from '@/store/user';
import {ElMessage} from 'element-plus';
import {fetchChatHistory, uploadChatFile} from '@/api/chatroom';
import {Folder, Picture} from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const props = defineProps({
  roomId: {
    type: [String, Number],
    required: true
  }
});

const emit = defineEmits(['message-context-menu']);

const userStore = useUserStore();
const socket = ref(null);
const messages = ref([]);
const newMessage = ref('');
const loading = ref(true);
const messageAreaRef = ref(null);

const historyPage = ref(1);
const hasMoreHistory = ref(true); // 假定初始有更多历史
const historyLoading = ref(false);

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/chatroom/${props.roomId}/`;

  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => {
    loading.value = false;
    ElMessage.success('已进入聊天室');
    loadHistory(true);
  };

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'error') {
      ElMessage.error(data.message);
    } else {
      messages.value.push(data);
      scrollToBottom();
    }
  };

  socket.value.onclose = () => {
    ElMessage.warning('与聊天室的连接已断开');
  };

  socket.value.onerror = (error) => {
    ElMessage.error('连接发生错误');
    console.error('WebSocket Error:', error);
  };
};

// --- 这是修正后的核心函数 ---
const loadHistory = async (isInitial = false) => {
  if (!hasMoreHistory.value || historyLoading.value) return;
  historyLoading.value = true;
  try {
    // 假设API直接返回数组，我们不再关心分页对象结构
    const response = await fetchChatHistory(props.roomId, {page: historyPage.value});

    // 检查返回的是否是数组，并且有内容
    if (Array.isArray(response.data) && response.data.length > 0) {
      const oldMessages = response.data.reverse(); // API返回的是倒序，我们把它正过来
      messages.value = [...oldMessages, ...messages.value];
      historyPage.value++; // 假设每次请求都是新的一页
    } else {
      // 如果返回空数组或不是数组，说明没有更多历史记录了
      hasMoreHistory.value = false;
      if (!isInitial) {
        ElMessage.info('没有更早的消息了');
      }
    }

    // 如果是第一次加载，滚动到底部
    if (isInitial) {
      await nextTick();
      scrollToBottom();
    }
  } catch (error) {
    ElMessage.error('加载历史消息失败');
    console.error("History loading error:", error);
  } finally {
    historyLoading.value = false;
  }
};


const sendMessage = () => {
  if (!newMessage.value.trim() || !socket.value || socket.value.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.value.send(JSON.stringify({
    type: 'chat_message',
    message: newMessage.value
  }));
  newMessage.value = '';
};

const handleEnter = (event) => {
  if (!event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

const handleBeforeUpload = (file) => {
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    ElMessage.error('上传文件大小不能超过 10MB!');
  }
  return isLt10M;
};

const handleCustomUpload = async (options) => {
  const formData = new FormData();
  formData.append('file', options.file);
  try {
    await uploadChatFile(props.roomId, formData);
    ElMessage.info('文件已发送，后台处理中...');
  } catch (error) {
    ElMessage.error('文件发送失败: ' + (error.response?.data?.detail || error.message));
  }
};

const getMessageClass = (msg) => {
  if (!msg || !msg.author) return 'received'; // 容错处理
  return msg.author.user_id === userStore.user.id ? 'sent' : 'received';
};

const getRoleTagType = (role) => {
  return role === 'admin' ? 'danger' : 'info';
};

const formatTimestamp = (ts) => dayjs(ts).format('YYYY-MM-DD HH:mm');

const scrollToBottom = () => {
  nextTick(() => {
    if (messageAreaRef.value) {
      messageAreaRef.value.scrollTop = messageAreaRef.value.scrollHeight;
    }
  });
};

const handleContextMenu = (event, message) => {
  if (message.message_type !== 'system') {
    emit('message-context-menu', {event, message});
  }
};

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.close();
  }
});
</script>

<style scoped>
.chat-room-container {
  height: 70vh;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.chat-layout {
  height: 100%;
}

.message-area {
  padding: 10px;
  background-color: #f5f7fa;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.message-item {
  margin-bottom: 15px;
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-item.sent {
  align-self: flex-end;
  align-items: flex-end;
}

.message-item.received {
  align-self: flex-start;
  align-items: flex-start;
}

.author-info {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
  color: #888;
}

.sent .author-info {
  flex-direction: row-reverse;
}

.nickname {
  margin: 0 8px;
  font-weight: 500;
}

.message-content-wrapper {
  padding: 10px 15px;
  border-radius: 12px;
  word-break: break-all;
  white-space: pre-wrap;
}

.sent .message-content-wrapper {
  background-color: #85e085;
  color: #fff;
  border-top-right-radius: 0;
}

.received .message-content-wrapper {
  background-color: #ffffff;
  border-top-left-radius: 0;
}

.input-area {
  border-top: 1px solid var(--el-border-color-lighter);
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.send-button {
  position: absolute;
  bottom: 20px;
  right: 20px;
}

.history-loader {
  text-align: center;
  margin: 10px 0;
  color: #999;
  font-size: 12px;
}
</style>