<template>
  <el-menu
      :default-active="$route.path"
      class="sidebar-menu"
      router
  >
    <el-menu-item v-for="item in items" :key="item.path" :index="item.path">
      <div class="menu-item-container">
        <span class="menu-label">{{ item.label }}</span>

        <el-badge
            v-if="item.badge"
            :value="item.badge"
            :max="99"
            class="sidebar-badge"
        />
      </div>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    required: true
  }
})
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  border-right: none; /* 通常布局中侧边栏的边框由外部容器提供 */
}

.menu-item-container {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 8px; /* 控制元素间距 */
}

.menu-label {
  /* 标签文本默认占据可用空间 */
}

.sidebar-badge {
  margin: 0;
  margin-left: 1px; /* 角标靠右对齐 */
  font-size: 12px; /* 调整角标字体大小 */
  line-height: 1; /* 确保角标垂直居中 */
}
</style>