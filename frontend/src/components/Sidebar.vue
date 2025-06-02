<template>
  <!-- Element Plus 菜单组件，绑定路由 -->
  <el-menu class="sidebar-menu" :default-active="$route.path" router>
    <el-menu-item
      v-for="item in items"
      :key="item.path"
      :index="item.path">
      {{ item.label }}
    </el-menu-item>
  </el-menu>
</template>

<script>
export default {
  name: 'Sidebar',
  props: {
    items: {
      type: Array,
      required: true
    }
  }
}
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  border-right: 1px solid #ebebeb;
}
</style>
