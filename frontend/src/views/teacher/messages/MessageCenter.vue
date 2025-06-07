<template>
  <div class="message-center-layout">
    <el-container style="height: 100%;">
      <el-aside width="220px" class="navigation-aside">
        <el-button
            type="primary"
            class="compose-btn"
            @click="$router.push({ name: 'TeacherMessageCompose' })"
            :icon="Edit"
        >
          写信息
        </el-button>
        <el-menu
            :default-active="$route.path"
            router
            class="message-menu"
        >
          <el-menu-item index="/teacher/messages/inbox">
            <div class="menu-item-content">
              <el-icon>
                <MessageBox/>
              </el-icon>
              <span>收件箱</span>
            </div>
            <el-badge
                :value="notificationStore.unreadCount"
                :max="99"
                class="menu-badge"
                :hidden="notificationStore.unreadCount === 0"
            />
          </el-menu-item>

            <el-menu-item index="/teacher/messages/sent">
              <div class="menu-item-content">
                <el-icon>
                  <Promotion/>
                </el-icon>
                <span>已发送</span>
              </div>
            </el-menu-item>

          <el-menu-item index="/teacher/messages/settings">
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
        <router-view v-slot="{ Component }">
          <keep-alive>
            <component :is="Component"/>
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { Edit, MessageBox, Setting, Promotion } from '@element-plus/icons-vue'
import {useNotificationStore} from '@/store/notifications'

const notificationStore = useNotificationStore()
</script>

<style scoped>
.message-center-layout {
  height: calc(100vh - 90px); /* 减去顶部和父级padding */
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
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

/* --- 核心修正样式 --- */
.el-menu-item {
  display: flex; /* 确认 flex 布局 */
  justify-content: space-between; /* 两端对齐 */
  align-items: center;
}

.menu-item-content {
  display: flex;
  align-items: center;
}

.menu-item-content .el-icon {
  margin-right: 8px; /* 图标和文字的间距 */
}

.menu-badge {
  margin-left: 10px; /* 和左侧内容的间距 */
}

/* --- 核心修正样式结束 --- */

.content-main {
  padding: 20px;
}
</style>