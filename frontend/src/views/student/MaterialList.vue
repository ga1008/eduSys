<template>
  <div class="material-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>{{ courseName }} - 课程资源</h3>
          <div class="filter-group">
            <el-input
              v-model="searchKey"
              placeholder="搜索资源名称"
              clearable
              style="width: 200px; margin-right: 10px;"
              @clear="fetchMaterials"
              @keyup.enter="fetchMaterials"
            />
            <el-select
              v-model="materialType"
              placeholder="资源类型"
              clearable
              @change="fetchMaterials"
            >
              <el-option
                v-for="type in materialTypes"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="materials" v-loading="loading">
        <el-table-column prop="title" label="资源名称" min-width="200">
          <template #default="{row}">
            <div class="material-title">
              <el-icon :color="getFileType(row).color" style="margin-right: 8px">
                <component :is="getFileType(row).icon" />
              </el-icon>
              {{ row.title }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_by_name" label="上传者" width="120" />
        <el-table-column prop="material_type" label="类型" width="100">
          <template #default="{row}">
            <el-tag :type="typeTagMap[row.material_type] || 'info'">
              {{ materialTypeLabels[row.material_type] || '其他' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="100">
          <template #default="{row}">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180">
          <template #default="{row}">
            {{ formatDateTime(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{row}">
            <el-button
              type="primary"
              size="small"
              @click="downloadMaterial(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  Folder,
  VideoPlay,
  Download,
  Picture
} from '@element-plus/icons-vue'
// 使用student.js中的方法，移除直接导入couRequest
import { fetchCourseMaterials, downloadCourseMaterial } from '@/api/student'

const route = useRoute()
const loading = ref(false)
const materials = ref([])
const searchKey = ref('')
const materialType = ref('')
const courseName = ref('')

// 资源类型配置
const materialTypes = [
  { value: 'lecture', label: '课件' },
  { value: 'reference', label: '参考资料' },
  { value: 'software', label: '软件' },
  { value: 'video', label: '视频' },
  { value: 'other', label: '其他' }
]

const typeTagMap = {
  lecture: 'success',
  reference: 'warning',
  software: 'danger',
  video: 'primary'
}

const materialTypeLabels = materialTypes.reduce((acc, cur) => {
  acc[cur.value] = cur.label
  return acc
}, {})

// 文件类型图标映射
const fileTypeIcons = {
  pdf: { icon: Document, color: '#f40f02' },
  ppt: { icon: Folder, color: '#d24726' },
  doc: { icon: Document, color: '#2b579a' },
  xls: { icon: Document, color: '#217346' },
  zip: { icon: Folder, color: '#7a7a7a' },
  video: { icon: VideoPlay, color: '#00a1d6' },
  image: { icon: Picture, color: '#4caf50' },
  default: { icon: Download, color: '#909399' }
}

const getFileType = (material) => {
  const ext = material.file.split('.').pop().toLowerCase()
  if (['mp4', 'avi', 'mov'].includes(ext)) return fileTypeIcons.video
  if (['jpg', 'png', 'gif'].includes(ext)) return fileTypeIcons.image
  if (ext === 'pdf') return fileTypeIcons.pdf
  if (['ppt', 'pptx'].includes(ext)) return fileTypeIcons.ppt
  if (['doc', 'docx'].includes(ext)) return fileTypeIcons.doc
  if (['xls', 'xlsx'].includes(ext)) return fileTypeIcons.xls
  if (['zip', 'rar'].includes(ext)) return fileTypeIcons.zip
  return fileTypeIcons.default
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '未设置'

  try {
    const date = new Date(dateStr)

    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.error('无效日期:', dateStr)
      return '日期格式错误'
    }

    // 获取星期几（0-6，0表示星期日）
    const day = date.getDay()
    // 中文星期映射
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']

    return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}（星期${weekDays[day]}） ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  } catch (error) {
    console.error('格式化日期出错:', error)
    return '日期格式错误'
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const downloadMaterial = async (material) => {
  try {
    // 使用student.js中的方法
    const response = await downloadCourseMaterial(material.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', material.file_name)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const fetchMaterials = async () => {
  try {
    loading.value = true
    // 使用student.js中的方法
    const { data } = await fetchCourseMaterials(route.params.id, {
      search: searchKey.value,
      type: materialType.value
    })
    materials.value = data.materials
    courseName.value = data.course_name
  } catch (error) {
    ElMessage.error('加载资源失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchMaterials)
</script>

<style scoped>
.material-title {
  display: flex;
  align-items: center;
}
.filter-group {
  display: flex;
  gap: 10px;
}
</style>