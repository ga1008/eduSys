<template>
  <el-menu class="sidebar-menu" :default-active="$route.path" router>
    <el-menu-item
        v-for="item in items"
        :key="item.path"
        :index="item.path">
      <div class="menu-item-content">
        <span>{{ item.label }}</span>
        <el-badge
            v-if="item.badge"
            :value="item.badge"
            :max="99"
            class="menu-item-badge"
        />
      </div>
    </el-menu-item>
  </el-menu>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    items: {
      type: Array,
      required: true // props 保持不变
    }
  }
}
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  border-right: 1px solid #ebebeb;
}

.menu-item-content {
  display: flex;
  justify-content: space-between; /* 让标题和角标分布在两侧 */
  align-items: center;
  width: 100%;
}

.menu-item-badge {
  margin-left: 10px;
}
</style>