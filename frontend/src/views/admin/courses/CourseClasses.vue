<template>
  <div>
    <el-card class="mb-4">
      <template #header>
        <span>课程：{{ courseName || `ID:${courseId}` }} — 班级管理</span>
        <div class="button-group">
          <el-button size="small" type="primary" @click="openBindForm()">添加班级绑定</el-button>
        </div>
      </template>

      <el-input v-model="searchKey" placeholder="搜索班级名称/教师姓名" clearable class="mb-3"/>

      <el-table :data="filteredBindings" border v-loading="loading">
        <el-table-column type="index" width="60"/>
        <el-table-column prop="class_obj.name" label="班级名称" :formatter="formatClass"/>
        <el-table-column prop="teacher.name" label="授课教师" :formatter="formatTeacher"/>
        <el-table-column prop="textbook" label="教材"/>
        <el-table-column prop="syllabus" label="教学大纲" show-overflow-tooltip/>
        <el-table-column prop="progress" label="教学进度"/>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="openBindForm(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeBinding(scope.row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑课程班级绑定' : '添加课程班级绑定'">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="课程" v-if="!isEdit">
          <el-input v-model="courseName" disabled/>
        </el-form-item>
        <el-form-item label="班级" prop="class_obj" v-if="!isEdit">
          <el-select v-model="form.class_obj" filterable placeholder="选择班级">
            <el-option
              v-for="item in classes"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" prop="teacher">
          <el-select v-model="form.teacher" filterable placeholder="选择教师">
            <el-option
              v-for="item in teachers"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="教材" prop="textbook">
          <el-input v-model="form.textbook" placeholder="请输入教材名称"/>
        </el-form-item>
        <el-form-item label="教学大纲" prop="syllabus">
          <el-input v-model="form.syllabus" type="textarea" rows="3" placeholder="请输入教学大纲"/>
        </el-form-item>
        <el-form-item label="教学进度" prop="progress">
          <el-input v-model="form.progress" placeholder="请输入当前教学进度"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveBinding">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchCourses, fetchCourse, fetchCourseClasses,
  createTeacherCourseClass, updateTeacherCourseClass, deleteTeacherCourseClass
} from '@/api/courses'
import { fetchClasses } from '@/api/classes'
import { fetchTeachers } from '@/api/teachers'

const props = defineProps({ courseId: [String, Number] })
const route = useRoute()
const courseId = props.courseId ?? route.params.id

const bindings = ref([])
const loading = ref(false)
const searchKey = ref('')
const courseName = ref('')
const classes = ref([])
const teachers = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = ref({
  course: courseId,
  class_obj: '',
  teacher: '',
  textbook: '',
  syllabus: '',
  progress: ''
})

const rules = {
  class_obj: [{ required: true, message: '请选择班级', trigger: 'change' }],
  teacher: [{ required: true, message: '请选择教师', trigger: 'change' }]
}

// 加载课程信息
const loadCourseInfo = async () => {
  try {
    const { data } = await fetchCourse(courseId)
    courseName.value = data.name
  } catch (e) {
    console.error('获取课程信息失败', e)
    ElMessage.error('获取课程信息失败')
  }
}

// 加载绑定列表
const loadBindings = async () => {
  try {
    const { data } = await fetchCourseClasses(courseId)
    // 转换数据结构以适配前端显示逻辑
    bindings.value = Array.isArray(data) ? data.map(item => ({
      ...item,
      class_obj: { id: item.class_obj, name: item.class_name },
      teacher: { id: item.teacher, name: item.teacher_name }
    })) : []
  } catch (e) {
    console.error('获取班级绑定失败', e)
    ElMessage.error('获取班级绑定失败')
  }
}

// 加载班级列表
const loadClasses = async () => {
  try {
    const { data } = await fetchClasses()
    classes.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch (e) {
    console.error('获取班级列表失败', e)
    ElMessage.error('获取班级列表失败')
  }
}

// 加载教师列表
const loadTeachers = async () => {
  try {
    const { data } = await fetchTeachers()
    teachers.value = Array.isArray(data) ? data : (data.results ?? [])
  } catch (e) {
    console.error('获取教师列表失败', e)
    ElMessage.error('获取教师列表失败')
  }
}

onMounted(async () => {
  await loadCourseInfo()
  await Promise.all([loadBindings(), loadClasses(), loadTeachers()])
})

// 筛选绑定数据
const filteredBindings = computed(() => {
  if (!searchKey.value) return bindings.value

  const q = searchKey.value.toLowerCase()
  return bindings.value.filter(b =>
    (b.class_obj?.name && b.class_obj.name.toLowerCase().includes(q)) ||
    (b.teacher?.name && b.teacher.name.toLowerCase().includes(q))
  )
})

// 格式化班级显示
const formatClass = (row) => {
  return row.class_obj?.name || '未知班级'
}

// 格式化教师显示
const formatTeacher = (row) => {
  return row.teacher?.name || '未设置教师'
}

// 打开��定表单
const openBindForm = (row = null) => {
  isEdit.value = !!row

  if (isEdit.value) {
    form.value = {
      id: row.id,
      course: courseId,
      class_obj: row.class_obj?.id,
      teacher: row.teacher?.id,
      textbook: row.textbook || '',
      syllabus: row.syllabus || '',
      progress: row.progress || ''
    }
  } else {
    form.value = {
      course: courseId,
      class_obj: '',
      teacher: '',
      textbook: '',
      syllabus: '',
      progress: ''
    }
  }

  dialogVisible.value = true
}

// 保存绑定
const saveBinding = async () => {
  try {
    await formRef.value.validate()

    if (isEdit.value) {
      await updateTeacherCourseClass(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createTeacherCourseClass(form.value)
      ElMessage.success('绑定成功')
    }

    dialogVisible.value = false
    await loadBindings()
  } catch (e) {
    if (e !== false) {
      console.error(e)
      ElMessage.error('保存失败: ' + (e.response?.data?.detail || '未知错误'))
    }
  }
}

// 删除绑定
const removeBinding = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定解除课程 "${courseName.value}" 与班级 "${row.class_obj?.name || '未知班级'}" 的绑定关系吗？`,
      '警告',
      { type: 'warning' }
    )

    await deleteTeacherCourseClass(row.id)
    ElMessage.success('解绑成功')
    await loadBindings()
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
      ElMessage.error('解绑失败: ' + (e.response?.data?.detail || '未知错误'))
    }
  }
}
</script>

<style scoped>
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }
.button-group {
  float: right;
}
</style>