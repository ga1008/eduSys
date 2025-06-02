<template>
  <el-table :data="submissions" size="small" border>
    <el-table-column prop="submit_time" label="提交时间" width="165">
      <template #default="{ row }">{{ dayjs(row.submit_time).format('YYYY-MM-DD HH:mm') }}</template>
    </el-table-column>

    <el-table-column prop="score" label="分数" width="70">
      <template #default="{ row }">
        <el-tag v-if="row.score !== null" type="success">{{ row.score }}</el-tag>
        <el-tag v-else type="info">未批</el-tag>
      </template>
    </el-table-column>

    <el-table-column prop="teacher_comment" label="评语" />

    <el-table-column label="操作" width="210" fixed="right">
      <template #default="{ row }">
        <el-button size="small" @click="$emit('load', row)">载入编辑</el-button>
        <el-popconfirm
          title="撤回并删除该提交？"
          @confirm="$emit('delete', row)"
        >
          <template #reference>
            <el-button size="small" type="danger">撤回</el-button>
          </template>
        </el-popconfirm>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import dayjs from 'dayjs'
defineProps({
  submissions: { type: Array, default: () => [] }
})

// 点击撤回时刷新页面
const { emit } = defineEmits(['delete'])

</script>
