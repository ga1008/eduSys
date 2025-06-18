<template>
  <div class="comment-composer">
    <el-input
        ref="inputRef"
        v-model="content"
        type="textarea"
        :placeholder="placeholder"
        :rows="3"
        :disabled="isSubmitting"
        show-word-limit
        maxlength="500"
    />
    <div class="comment-actions">
      <el-button @click="cancel" size="small" plain>取消</el-button>
      <el-button
          @click="submit"
          size="small"
          type="primary"
          :loading="isSubmitting"
          :disabled="!content.trim()"
      >
        发布
      </el-button>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue';

// 定义 props 和 emits
const props = defineProps({
  placeholder: {
    type: String,
    default: '发表你的看法...',
  },
  isSubmitting: Boolean,
});

const emit = defineEmits(['submit', 'cancel']);

const content = ref('');
const inputRef = ref(null);

// 提交评论，只发出内容，由父组件处理具体逻辑
const submit = () => {
  if (!content.value.trim()) {
    return;
  }
  emit('submit', content.value);
  content.value = ''; // 提交后清空
};

// 取消评论
const cancel = () => {
  emit('cancel');
  content.value = ''; // 取消后清空
};

// 组件挂载后自动聚焦输入框
onMounted(() => {
  inputRef.value?.focus();
});
</script>

<style scoped>
.comment-composer {
  margin-top: 12px;
}

.comment-actions {
  margin-top: 8px;
  text-align: right;
}
</style>