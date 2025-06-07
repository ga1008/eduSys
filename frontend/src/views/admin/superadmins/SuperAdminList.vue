<template>
  <div>
    <h2>超级管理员管理</h2>

    <div class="toolbar">
      <el-button type="primary" @click="router.push('/admin/superadmins/new')">新增管理员</el-button>
      <el-input v-model="searchQuery" placeholder="搜索管理员..." clearable style="width:260px"/>
    </div>

    <el-table :data="filteredAdmins" border v-loading="loading" style="width:100%">
      <el-table-column prop="id" label="ID" width="80"/>
      <el-table-column prop="username" label="用户名" width="150"/>
      <el-table-column prop="name" label="姓名" width="150"/>
      <el-table-column prop="gender" label="性别" width="80">
        <template #default="scope">{{ formatGender(scope.row.gender) }}</template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱"/>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" type="primary" @click="router.push(`/admin/superadmins/${scope.row.id}/edit`)"
                     :disabled="isSelf(scope.row.id)">编辑
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)" :disabled="isSelf(scope.row.id)">删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import {ref, computed, onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {useUserStore} from '@/store/user'
import {fetchSuperAdmins, deleteSuperAdmin} from '@/api/superadmins'
import {ElMessage, ElMessageBox} from 'element-plus'

const router = useRouter();
const userStore = useUserStore();
const admins = ref([]);
const loading = ref(false);
const searchQuery = ref('');

const currentUser = computed(() => userStore.user);
const isSelf = (id) => currentUser.value?.id === id;

const loadAdmins = async () => {
  loading.value = true;
  try {
    const {data} = await fetchSuperAdmins();
    admins.value = data;
  } catch (error) {
    ElMessage.error('获取管理员列表失败');
  } finally {
    loading.value = false;
  }
};

const formatGender = (gender) => ({'M': '男', 'F': '女', 'O': '其他'}[gender] || '未知');

const filteredAdmins = computed(() => {
  if (!searchQuery.value) return admins.value;
  const query = searchQuery.value.toLowerCase();
  return admins.value.filter(admin =>
      (admin.name && admin.name.toLowerCase().includes(query)) ||
      (admin.username && admin.username.toLowerCase().includes(query)) ||
      (admin.email && admin.email.toLowerCase().includes(query))
  );
});

const handleDelete = async (admin) => {
  try {
    await ElMessageBox.confirm(`确定删除超级管理员「${admin.name || admin.username}」吗？此操作不可逆！`, '严重警告', {type: 'warning'});
    await deleteSuperAdmin(admin.id);
    ElMessage.success('删除成功');
    await loadAdmins();
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

onMounted(loadAdmins);
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin: 16px 0;
}
</style>