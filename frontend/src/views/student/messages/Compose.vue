<template>
  <div>
    <h2>写新消息</h2>
    <el-form :model="form" label-width="80px" class="compose-form">
      <el-form-item label="收件人" prop="recipient">
        <el-select
            v-model="form.recipient"
            filterable remote reserve-keyword
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
      <el-form-item label="主题" prop="title">
        <el-input v-model="form.title" placeholder="请输入消息主题"/>
      </el-form-item>
      <el-form-item label="内容" prop="content">
        <v-md-editor
            v-model="form.content"
            height="400px"
            placeholder="在这里输入消息内容，支持 Markdown 格式..."
        ></v-md-editor>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSend" :loading="sending">
          立即发送
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {ref} from 'vue';
import {useRouter} from 'vue-router';
import {searchUsers, sendMessage} from '@/api/notifications';
import {ElMessage} from 'element-plus';

// --- v-md-editor ---
// 1. 引入 v-md-editor 组件及样式
import VMdEditor from '@kangc/v-md-editor/lib/base-editor';
import '@kangc/v-md-editor/lib/style/base-editor.css';
// 2. 引入主题
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import '@kangc/v-md-editor/lib/theme/style/github.css';
// 3. 引入代码高亮插件
import Prism from 'prismjs';
// ---

// 4. 使用主题和高亮插件
VMdEditor.use(githubTheme, {
  Prism,
});

const router = useRouter();
const form = ref({
  recipient: '',
  title: '',
  content: '' // 现在这里直接就是 Markdown 字符串
});
const searchLoading = ref(false);
const sending = ref(false);
const userOptions = ref([]);

const searchUsersRemote = async (query) => {
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

const handleSend = async () => {
  // 优化验证逻辑，直接检查 Markdown 内容是否为空
  if (!form.value.recipient || !form.value.title.trim() || !form.value.content.trim()) {
    ElMessage.warning('收件人、主题和内容均不能为空');
    return;
  }
  sending.value = true;
  try {
    // 直接发送 form.value，因为 content 已经是 Markdown 格式
    await sendMessage(form.value);
    ElMessage.success('发送成功');
    router.push({name: 'StudentMessageInbox'});
  } finally {
    sending.value = false;
  }
};
</script>

<style scoped>
.compose-form {
  max-width: 960px; /* 为表单设置一个最大宽度，提升大屏下的观感 */
  margin: 0 auto;
}

/* 调整表单项间距 */
.el-form-item {
  margin-bottom: 22px;
}
</style>