<!--跟班级关联的课程-->
<!--课程管理页面-->
<template>
  <div>
    <h1>课程管理</h1>

    <!-- 课程基础信息管理部分 -->
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <h3>课程基础信息管理</h3>
          <el-button type="primary" @click="addCourseBase">新增课程</el-button>
        </div>
      </template>

      <el-table :data="coursesList" border style="width: 100%" v-loading="coursesLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="课程名称" />
        <el-table-column prop="code" label="课程代码" />
        <el-table-column prop="credit" label="学分" />
        <el-table-column prop="hours" label="课时" />
        <el-table-column prop="description" label="课程描述" show-overflow-tooltip />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editCourseBase(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCourseBase(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 课程绑定管理部分 -->
    <el-card class="mb-4">
      <template #header>
        <div class="card-header">
          <h3>课程班级绑定管理</h3>
          <div>
            <el-button type="primary" @click="addCourse">新增课程绑定</el-button>
            <el-input v-model="searchQuery" placeholder="搜索..." class="search-input" clearable @input="handleSearch" />
          </div>
        </div>
      </template>

      <el-table :data="courses" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column label="教师">
          <template #default="scope">
            {{ getTeacherName(scope.row.teacher) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editCourse(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCourse(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页控件 -->
      <el-pagination
        v-if="totalItems > 0"
        layout="total, prev, pager, next"
        :total="totalItems"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        class="mt-4"
      />
    </el-card>

    <!-- 课程基础信息对话框 -->
    <el-dialog v-model="courseBaseDialogVisible" :title="isEditBase ? '编辑课程' : '新增课程'">
      <el-form :model="courseBaseForm" label-width="80px" ref="courseBaseFormRef" :rules="courseBaseRules">
        <el-form-item label="课程名称" prop="name">
          <el-input v-model="courseBaseForm.name" placeholder="请输��课程名称"></el-input>
        </el-form-item>
        <el-form-item label="课程代码" prop="code">
          <el-input v-model="courseBaseForm.code" placeholder="请输入课程代码"></el-input>
        </el-form-item>
        <el-form-item label="学分" prop="credit">
          <el-input-number v-model="courseBaseForm.credit" :min="0" :max="10" :precision="1"></el-input-number>
        </el-form-item>
        <el-form-item label="课时" prop="hours">
          <el-input-number v-model="courseBaseForm.hours" :min="0" :max="200"></el-input-number>
        </el-form-item>
        <el-form-item label="课程描述" prop="description">
          <el-input type="textarea" v-model="courseBaseForm.description" rows="3" placeholder="请输入课程描述"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="courseBaseDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCourseBase">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 课程绑定对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑课程绑定' : '新增课程绑定'">
      <el-form :model="form" label-width="80px" ref="formRef">
        <el-form-item label="课程" prop="course" :rules="[{ required: true, message: '请选择课程' }]">
          <el-select v-model="form.course" placeholder="请选择课程" filterable>
            <el-option
              v-for="course in allCourses"
              :key="course.id"
              :label="course.name"
              :value="course.id">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="班级" prop="class_obj" :rules="[{ required: true, message: '请选择班级' }]">
          <el-select v-model="form.class_obj" placeholder="请选择班级" filterable>
            <el-option
              v-for="classItem in classes"
              :key="classItem.id"
              :label="classItem.name"
              :value="classItem.id">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="教师" prop="teacher" :rules="[{ required: true, message: '请选择教师' }]">
          <el-select v-model="form.teacher" placeholder="选择教师" filterable>
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="教材" prop="textbook">
          <el-input v-model="form.textbook" placeholder="请输入教材名称"></el-input>
        </el-form-item>

        <el-form-item label="教学大纲" prop="syllabus">
          <el-input type="textarea" v-model="form.syllabus" rows="3" placeholder="请输入教学大纲"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCourse">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import apiClient from '@/api/axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useUserStore } from '@/store/user';
import couApiClient from "@/api/axios_cou";

const userStore = useUserStore();
const courses = ref([]);
const allCourses = ref([]);
const classes = ref([]);
const teachers = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const dialogVisible = ref(false);
const isEdit = ref(false);
const formRef = ref(null);
const totalItems = ref(0);
const pageSize = ref(10);
const currentPage = ref(1);

// 课程基础信息相关
const coursesList = ref([]);
const coursesLoading = ref(false);
const courseBaseDialogVisible = ref(false);
const isEditBase = ref(false);
const courseBaseFormRef = ref(null);
const courseBaseForm = ref({
  id: null,
  name: '',
  code: '',
  credit: 1,
  hours: 16,
  description: ''
});

// 课程表单验证规则
const courseBaseRules = {
  name: [
    { required: true, message: '请输入课程名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入课程代码', trigger: 'blur' }
  ],
  credit: [
    { required: true, message: '请输入学分', trigger: 'blur' }
  ],
  hours: [
    { required: true, message: '请输入学时', trigger: 'blur' }
  ]
};

// 绑定表单
const form = ref({
  id: null,
  course: '',
  class_obj: '',
  teacher: '',
  textbook: '',
  syllabus: ''
});

// 根据教师ID获取教师名称
const getTeacherName = (teacherId) => {
  const teacher = teachers.value.find(t => t.id === teacherId);
  return teacher ? teacher.name : '未知教师';
};

// 获取课程列表
const fetchCourses = async () => {
  loading.value = true;
  try {
    const response = await couApiClient.get('/teacher-course-classes/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search: searchQuery.value
      }
    });

    if (response.data.results) {
      courses.value = response.data.results;
      totalItems.value = response.data.count;
    } else {
      courses.value = response.data;
    }
  } catch (error) {
    console.error('获取课程列表失败', error);
    ElMessage.error('获取课程列表失败: ' + (error.response?.data?.detail || '未知错误'));
  } finally {
    loading.value = false;
  }
};

// 获取课程基础信息列表
const fetchCoursesList = async () => {
  coursesLoading.value = true;
  try {
    const response = await couApiClient.get('/courses/');
    coursesList.value = response.data;
  } catch (error) {
    console.error('获取课程基础信息失败', error);
    ElMessage.error('获取课程基础信息失败: ' + (error.response?.data?.detail || '未知错误'));
  } finally {
    coursesLoading.value = false;
  }
};

// 获取所有课程基础信息（用于选择器）
const fetchAllCourses = async () => {
  try {
    const response = await couApiClient.get('/courses/');
    allCourses.value = response.data;
  } catch (error) {
    console.error('获取所有课程失败', error);
    ElMessage.error('获取所有课程失败');
  }
};

// 获取所有班级
const fetchClasses = async () => {
  try {
    const response = await apiClient.get('/classes/');
    classes.value = response.data;
  } catch (error) {
    console.error('获取班级列表失败', error);
    ElMessage.error('获取班级列表失败');
  }
};

// 获取所有教师
const fetchTeachers = async () => {
  try {
    const response = await apiClient.get('/teachers/');
    teachers.value = response.data;
  } catch (error) {
    console.error('获取教师列表失败', error);
    ElMessage.error('获取教师列表失败');
  }
};

// 搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchCourses();
};

// 分页
const handlePageChange = (page) => {
  currentPage.value = page;
  fetchCourses();
};

// 新增课程基础信息
const addCourseBase = () => {
  isEditBase.value = false;
  courseBaseForm.value = {
    name: '',
    code: '',
    credit: 1,
    hours: 16,
    description: ''
  };
  courseBaseDialogVisible.value = true;
};

// 编辑课程基础信息
const editCourseBase = (course) => {
  isEditBase.value = true;
  courseBaseForm.value = { ...course };
  courseBaseDialogVisible.value = true;
};

// 保存课程基础信息
const saveCourseBase = async () => {
  try {
    await courseBaseFormRef.value.validate();

    if (isEditBase.value) {
      // 编辑现有课程
      await couApiClient.put(`/courses/${courseBaseForm.value.id}/`, courseBaseForm.value);
      ElMessage.success('课程更新成功');
    } else {
      // 创建新课程
      await couApiClient.post('/courses/', courseBaseForm.value);
      ElMessage.success('课程创建成功');
    }

    courseBaseDialogVisible.value = false;
    fetchCoursesList(); // 刷新课程列表
    fetchAllCourses(); // 刷新课程选择器数据
  } catch (error) {
    if (error === false) return; // 表单验证失败
    console.error('保存课程失败', error);
    ElMessage.error('保存失败：' + (error.response?.data?.detail || '请检查表单数据'));
  }
};

// 删除课程基础信息
const deleteCourseBase = async (course) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除课程 "${course.name}" 吗? 这将同时删除所有关联的课程绑定关系。`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await couApiClient.delete(`/courses/${course.id}/`);
    ElMessage.success('课程删除成功');
    fetchCoursesList(); // 刷新课程列表
    fetchCourses(); // 刷新课程绑定列表
    fetchAllCourses(); // 刷新课程选择器数据
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除课程失败', error);
      ElMessage.error('删除失败：' + (error.response?.data?.detail || '未知错误'));
    }
  }
};

// 新增课程绑定
const addCourse = () => {
  isEdit.value = false;
  form.value = {
    course: '',
    class_obj: '',
    teacher: '',
    textbook: '',
    syllabus: ''
  };
  dialogVisible.value = true;
};

// 编辑课程绑定
const editCourse = (course) => {
  isEdit.value = true;
  form.value = {
    id: course.id,
    course: course.course.id,
    class_obj: course.class_obj.id,
    teacher: course.teacher,
    textbook: course.textbook || '',
    syllabus: course.syllabus || ''
  };
  dialogVisible.value = true;
};

// 保存课程绑定
const saveCourse = async () => {
  try {
    await formRef.value.validate();

    const formData = {
      course: form.value.course,
      class_obj: parseInt(form.value.class_obj),
      teacher: form.value.teacher,
      textbook: form.value.textbook,
      syllabus: form.value.syllabus
    };

    if (isEdit.value) {
      await couApiClient.put(`/teacher-course-classes/${form.value.id}/`, formData);
      ElMessage.success('课程绑定更新成功');
    } else {
      await couApiClient.post('/teacher-course-classes/', formData);
      ElMessage.success('课程绑定创建成功');
    }

    dialogVisible.value = false;
    fetchCourses();
  } catch (error) {
    if (error === false) return;
    console.error('保存课程绑定失败', error);
    ElMessage.error('保存失败：' + (error.response?.data?.detail || '请检查表单数据'));
  }
};

// 删除课程绑定
const deleteCourse = async (course) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${course.course.name}" 在 "${course.class_obj.name}" 班级的绑定吗?`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await couApiClient.delete(`/teacher-course-classes/${course.id}/`);
    ElMessage.success('删除成功');
    fetchCourses();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败', error);
      ElMessage.error('删除失败：' + (error.response?.data?.detail || '未知错误'));
    }
  }
};

// 组件加载时获取数据
onMounted(() => {
  fetchCourses();
  fetchCoursesList();
  fetchAllCourses();
  fetchClasses();
  fetchTeachers();
});
</script>

<style scoped>
.actions, .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.search-input {
  width: 300px;
  margin-left: 10px;
}
.mb-4 {
  margin-bottom: 20px;
}
</style>