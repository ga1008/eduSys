<template>
  <div class="message-center-layout">
    <el-container style="height: 100%;">
      <el-aside width="220px" class="navigation-aside">
        <el-button
            type="primary"
            class="compose-btn"
            @click="$router.push({ name: composeRouteName })"
            :icon="Edit"
        >
          写信息
        </el-button>
        <el-menu
            :default-active="$route.path"
            router
            class="message-menu"
        >
          <el-menu-item :index="inboxPath">
            <div class="menu-item-content">
              <el-icon>
                <MessageBox/>
              </el-icon>
              <span>收件箱</span>
              <el-badge
                  class="menu-badge"
                  :value="notificationStore.unreadCount"
                  :max="99"
                  :hidden="notificationStore.unreadCount === 0"
              />
            </div>
          </el-menu-item>

          <el-menu-item :index="sentPath">
            <div class="menu-item-content">
              <el-icon>
                <Promotion/>
              </el-icon>
              <span>已发送</span>
            </div>
          </el-menu-item>

          <el-menu-item :index="settingsPath">
            <div class="menu-item-content">
              <el-icon>
                <Setting/>
              </el-icon>
              <span>设置</span>
            </div>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="content-main">
        <router-view/>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import {computed} from 'vue';
import {useRoute} from 'vue-router';
import {Edit, MessageBox, Setting, Promotion} from '@element-plus/icons-vue';
import {useNotificationStore} from '@/store/notifications';

const notificationStore = useNotificationStore();
const route = useRoute();

// 根据当前路由动态判断是学生端还是教师端
const isStudent = computed(() => route.path.startsWith('/student'));
const basePath = computed(() => isStudent.value ? '/student' : '/teacher');

// 动态生成路由名称和路径
const composeRouteName = computed(() => isStudent.value ? 'StudentMessageCompose' : 'TeacherMessageCompose');
const inboxPath = computed(() => `${basePath.value}/messages/inbox`);
const sentPath = computed(() => `${basePath.value}/messages/sent`);
const settingsPath = computed(() => `${basePath.value}/messages/settings`);

</script>

<style scoped>
.message-center-layout {
  height: calc(100vh - 90px);
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.navigation-aside {
  border-right: 1px solid #e6e6e6;
  padding: 20px 0;
}

.compose-btn {
  width: 80%;
  margin-left: 10%;
  margin-bottom: 20px;
}

.message-menu {
  border-right: none;
}

.content-main {
  padding: 20px;
}

/* --- 核心修正样式 --- */
.menu-item-content {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px; /* 使用 gap 控制图标和文字的间距 */
}

.menu-badge {
  margin: 0;
  margin-left: 1px; /* 角标靠右对齐 */
  font-size: 12px; /* 调整角标字体大小 */
  line-height: 1; /* 确保角标垂直居中 */
}
</style>