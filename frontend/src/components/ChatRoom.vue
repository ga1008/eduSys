<template>
  <div class="chat-room-container" v-loading="loading" element-loading-text="正在进入聊天室...">
    <el-container class="chat-layout">
      <el-main class="message-area" ref="messageAreaRef">
        <div class="history-loader">
          <el-button v-if="hasMoreHistory && !historyLoading" @click="loadHistory()" size="small" round>
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
                  v-if="msg.thumbnail_path"
                  :src="msg.thumbnail_path"
                  :preview-src-list="[msg.file_path]"
                  class="chat-image" fit="cover" hide-on-click-modal preview-teleported lazy
              />
              <div v-else class="upload-placeholder">
                <el-icon class="is-loading">
                  <Loading/>
                </el-icon>
                <span>图片上传中...</span>
              </div>
            </div>

            <div v-else-if="msg.message_type === 'video'" class="message-content video"
                 @click="playVideo(msg.file_path)">
              <el-image v-if="msg.thumbnail_path" :src="msg.thumbnail_path" class="chat-image" fit="cover" lazy>
                <template #placeholder>
                  <div class="image-slot">加载中...</div>
                </template>
              </el-image>
              <div v-if="!msg.thumbnail_path" class="upload-placeholder">
                <el-icon class="is-loading">
                  <Loading/>
                </el-icon>
                <span>视频上传中...</span>
              </div>
              <div class="play-icon-overlay" v-if="msg.thumbnail_path">
                <el-icon size="40">
                  <VideoPlay/>
                </el-icon>
              </div>
            </div>

            <div v-else-if="msg.message_type === 'file'" class="message-content file">
              <div v-if="msg.file_path">
                <el-icon>
                  <Document/>
                </el-icon>
                <span class="file-name">{{ msg.file_original_name }}</span>
                <el-link :href="msg.file_path" type="primary" target="_blank" :underline="false"
                         style="margin-left: 10px;">
                  下载
                </el-link>
              </div>
              <div v-else class="upload-placeholder">
                <el-icon class="is-loading">
                  <Loading/>
                </el-icon>
                <span>文件上传中...</span>
              </div>
            </div>

            <div v-else-if="msg.message_type === 'system'" class="message-content system-message">
              {{ msg.content }}
            </div>
          </div>
        </div>
      </el-main>

      <el-footer class="input-area" height="auto">
        <div class="toolbar">
          <el-upload
              :show-file-list="false"
              :http-request="handleCustomUpload"
              :before-upload="handleBeforeUpload"
              multiple
          >
            <el-tooltip content="图片 / 视频" placement="top">
              <el-button :icon="Picture" circle></el-button>
            </el-tooltip>
          </el-upload>
          <el-upload
              :show-file-list="false"
              :http-request="handleCustomUpload"
              :before-upload="handleBeforeUpload"
              multiple
          >
            <el-tooltip content="文件" placement="top">
              <el-button :icon="Folder" circle></el-button>
            </el-tooltip>
          </el-upload>
        </div>
        <el-input
            v-model="newMessage"
            type="textarea"
            :rows="5"
            placeholder="输入消息内容，Shift + Enter 换行"
            resize="none"
            @keydown.enter="handleEnter"
        ></el-input>
        <div class="footer-actions">
          <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
      </el-footer>
    </el-container>

    <el-dialog v-model="videoDialogVisible" title="视频播放" width="60%" destroy-on-close center>
      <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay
             style="width: 100%; max-height: 70vh;"></video>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, nextTick} from 'vue';
import {useUserStore} from '@/store/user';
import {ElMessage, ElDialog} from 'element-plus';
import {uploadChatFile, fetchChatHistory} from '@/api/chatroom';
import {Folder, Picture, VideoPlay, Document, Loading} from '@element-plus/icons-vue';
import dayjs from 'dayjs';

const props = defineProps({roomId: {type: [String, Number], required: true}});
const emit = defineEmits(['message-context-menu']);

const userStore = useUserStore();
const socket = ref(null);
const messages = ref([]);
const newMessage = ref('');
const loading = ref(true);
const messageAreaRef = ref(null);

const historyPage = ref(1);
const hasMoreHistory = ref(true);
const historyLoading = ref(false);

const videoDialogVisible = ref(false);
const currentVideoUrl = ref('');

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
      return;
    }

    // --- 核心修正：处理消息更新 ---
    if (data.is_update) {
      const index = messages.value.findIndex(m => m.id === data.id);
      if (index !== -1) {
        messages.value.splice(index, 1, data);
      } else {
        messages.value.push(data);
      }
    } else {
      messages.value.push(data);
    }

    // 如果是自己发的消息，就滚动到底部
    if (data.author && data.author.user_id === userStore.user.id) {
      scrollToBottom();
    }
  };

  socket.value.onclose = () => ElMessage.warning('与聊天室的连接已断开');
  socket.value.onerror = (error) => {
    ElMessage.error('连接发生错误');
    console.error('WebSocket Error:', error);
  };
};

const loadHistory = async (isInitial = false) => {
  if (!hasMoreHistory.value || historyLoading.value) return;
  historyLoading.value = true;
  try {
    const response = await fetchChatHistory(props.roomId, {page: historyPage.value, page_size: 20});

    // --- 核心修正：兼容纯数组和分页对象 ---
    const responseData = response.data;
    const newMessages = Array.isArray(responseData) ? responseData : responseData.results || [];
    hasMoreHistory.value = Array.isArray(responseData) ? false : !!responseData.next;

    if (newMessages.length > 0) {
      messages.value = [...newMessages.reverse(), ...messages.value];
      historyPage.value++;
    }

    if (isInitial) {
      await nextTick();
      scrollToBottom();
    } else if (newMessages.length === 0) {
      ElMessage.info('没有更早的消息了');
    }

  } catch (error) {
    ElMessage.error('加载历史消息失败');
  } finally {
    historyLoading.value = false;
  }
};

const sendMessage = () => {
  if (!newMessage.value.trim() || !socket.value || socket.value.readyState !== WebSocket.OPEN) return;

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
  const isLt20M = file.size / 1024 / 1024 < 20;
  if (!isLt20M) {
    ElMessage.error('上传文件大小不能超过 20MB!');
  }
  return isLt20M;
};

// --- 核心修正：提供即时UI反馈 ---
const handleCustomUpload = async ({file}) => {
  const tempId = `temp_${Date.now()}_${file.name}`;
  const fileType = file.type.startsWith('image') ? 'image' : (file.type.startsWith('video') ? 'video' : 'file');

  const placeholderMessage = {
    id: tempId,
    author: {
      id: userStore.user.id,
      nickname: '我',
      role: userStore.user.role,
      user_id: userStore.user.id,
    },
    message_type: fileType,
    content: '上传中...',
    file_original_name: file.name,
    file_path: null,
    thumbnail_path: null,
    timestamp: new Date().toISOString(),
  };
  messages.value.push(placeholderMessage);
  scrollToBottom();

  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await uploadChatFile(props.roomId, formData);
    const realMessageId = response.data.message_id;

    const msgIndex = messages.value.findIndex(m => m.id === tempId);
    if (msgIndex !== -1) {
      messages.value[msgIndex].id = realMessageId;
    }

  } catch (error) {
    ElMessage.error(`文件 ${file.name} 发送失败`);
    const msgIndex = messages.value.findIndex(m => m.id === tempId);
    if (msgIndex !== -1) {
      messages.value.splice(msgIndex, 1);
    }
  }
};

const playVideo = (url) => {
  if (!url) return;
  currentVideoUrl.value = url;
  videoDialogVisible.value = true;
};

const getMessageClass = (msg) => {
  if (!msg || !msg.author) return 'received';
  return msg.author.user_id === userStore.user.id ? 'sent' : 'received';
};

const getRoleTagType = (role) => (role === 'admin' ? 'danger' : 'info');
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

onMounted(connectWebSocket);
onUnmounted(() => {
  if (socket.value) socket.value.close();
});
</script>


<style scoped>
.chat-room-container {
  height: 75vh;
  display: flex;
  flex-direction: column;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.chat-layout {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-area {
  flex-grow: 1;
  padding: 20px;
  background-color: #f5f7fa;
  overflow-y: auto;
}

.message-item {
  margin-bottom: 20px;
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
  color: #606266;
}

.message-content-wrapper {
  padding: 10px 15px;
  border-radius: 12px;
  word-break: break-all;
  white-space: pre-wrap;
  position: relative;
}

.sent .message-content-wrapper {
  background-color: #85e085;
  color: black;
}

.received .message-content-wrapper {
  background-color: #ffffff;
  border: 1px solid var(--el-border-color-extra-light);
  border-top-left-radius: 0;
}

.message-content.image, .message-content.video {
  padding: 0;
  background-color: transparent;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.chat-image {
  max-width: 250px;
  max-height: 250px;
  display: block;
}

.play-icon-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  color: white;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none; /* 让点击事件可以穿透到图片上 */
}

.upload-placeholder {
  width: 150px;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  border-radius: 8px;
  color: #909399;
}

.message-content.file {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-weight: 500;
}

.system-message {
  font-size: 12px;
  color: #909399;
  align-self: center;
  background-color: #e9e9eb;
  padding: 3px 8px;
  border-radius: 4px;
}

.input-area {
  padding: 10px;
  background: #fff;
  border-top: 1px solid var(--el-border-color-lighter);
  height: auto !important;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.history-loader {
  text-align: center;
  margin: 10px 0;
  color: #999;
  font-size: 12px;
}
</style>