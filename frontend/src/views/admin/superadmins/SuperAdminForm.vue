<template>
  <div>
    <h2>{{ isEdit ? '编辑超级管理员' : '添加超级管理员' }}</h2>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width: 600px"
             v-loading="loading">

      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" :disabled="isEdit" placeholder="用于登录，创建后不可修改"/>
      </el-form-item>

      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name"/>
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" type="email"/>
      </el-form-item>

      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password
                  :placeholder="isEdit ? '留空则不修改密码' : '请输入初始密码'"/>
      </el-form-item>

      <el-form-item label="性别" prop="gender">
        <el-select v-model="form.gender" placeholder="请选择性别">
          <el-option label="男" value="M"/>
          <el-option label="女" value="F"/>
          <el-option label="其他" value="O"/>
        </el-select>
      </el-form-item>

      <el-form-item label="电话" prop="phone">
        <el-input v-model="form.phone"/>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">保存</el-button>
        <el-button @click="goBack">返回</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue';
import {useRouter, useRoute} from 'vue-router';
import {fetchSuperAdmin, createSuperAdmin, updateSuperAdmin} from '@/api/superadmins';
import {ElMessage} from 'element-plus';

const router = useRouter();
const route = useRoute();
const formRef = ref(null);
const loading = ref(false);

const isEdit = computed(() => Boolean(route.params.id));

const form = reactive({
  username: '',
  name: '',
  email: '',
  password: '',
  gender: 'M',
  phone: ''
});

const rules = {
  username: [
    {required: true, message: '请输入用户名', trigger: 'blur'},
    {pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符', trigger: 'blur'}
  ],
  name: [{required: true, message: '请输入姓名', trigger: 'blur'}],
  email: [
    {required: true, message: '请输入邮箱', trigger: 'blur'},
    {type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur'}
  ],
  password: [
    // 编辑时非必填，创建时必填
    {required: !isEdit.value, message: '请输入初始密码', trigger: 'blur'},
    {min: 6, message: '密码长度不能少于6位', trigger: ['blur', 'change']}
  ],
  phone: [{pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur'}]
};

const loadAdmin = async () => {
  if (!isEdit.value) return;
  loading.value = true;
  try {
    const {data} = await fetchSuperAdmin(route.params.id);
    Object.assign(form, data);
    form.password = ''; // 清空密码字段，不显示
  } catch (error) {
    ElMessage.error('获取管理员信息失败');
  } finally {
    loading.value = false;
  }
};

const submitForm = async () => {
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      const formData = {...form};
      if (isEdit.value && !formData.password) {
        delete formData.password;
      }

      if (isEdit.value) {
        await updateSuperAdmin(route.params.id, formData);
        ElMessage.success('更新成功');
      } else {
        await createSuperAdmin(formData);
        ElMessage.success('添加成功');
      }
      goBack();
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || (isEdit.value ? '更新失败' : '添加失败'));
    } finally {
      loading.value = false;
    }
  });
};

const goBack = () => {
  router.push('/admin/superadmins');
};

onMounted(loadAdmin);
</script>