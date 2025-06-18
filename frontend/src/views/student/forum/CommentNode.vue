<template>
  <div
      class="comment-node"
      :class="{'reply-highlight': activeReply && activeReply.id === comment.id}"
      :ref="(el) => registerRef(comment.id, el)"
  >
    <div class="comment-header">
      <el-avatar :size="32" :src="comment.author.avatar || defaultAvatar"/>
      <div class="author-info">
        <span class="author-name">{{ getAuthorName(comment.author) }}</span>
        <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
      </div>
      <div class="comment-actions">
        <el-button
            @click="like"
            :type="comment.is_liked ? 'primary' : 'default'"
            size="small"
            text
        >
          <el-icon>
            <CaretTop/>
          </el-icon>
          <span>{{ comment.like_count > 0 ? comment.like_count : '赞' }}</span>
        </el-button>
        <el-button
            @click="reply"
            size="small"
            type="text"
        >
          回复
        </el-button>
      </div>
    </div>
    <div class="comment-content" v-html="comment.content"></div>

    <transition name="fade-slide">
      <div
          v-if="activeReply && activeReply.id === comment.id"
          class="comment-composer-wrapper"
      >
        <CommentComposer
            :placeholder="`回复 @${getAuthorName(comment.author)}`"
            :is-submitting="isSubmitting"
            @submit="submitReply"
            @cancel="cancelReply"
        />
      </div>
    </transition>

    <div class="replies-list" v-if="comment.replies && comment.replies.length">
      <CommentNode
          v-for="reply in comment.replies"
          :key="reply.id"
          :comment="reply"
          :active-reply="activeReply"
          :is-submitting="isSubmitting"
          :register-ref="registerRef"
          @reply="emit('reply', $event)"
          @submit="submitReply"
          @cancel="cancelReply"
          @like="emit('like', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import {defineProps, defineEmits} from 'vue';
import {CaretTop} from '@element-plus/icons-vue';
import CommentComposer from './CommentComposer.vue';
import dayjs from 'dayjs';

const props = defineProps({
  comment: Object,
  activeReply: Object,
  isSubmitting: Boolean,
  registerRef: Function,
});

// 新增了 'like' 事件
const emit = defineEmits(['reply', 'submit', 'cancel', 'like']);

const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const submitReply = (content) => emit('submit', content);
const cancelReply = () => emit('cancel');
const reply = () => emit('reply', props.comment.id);
// 新增：发出点赞事件，将整个comment对象传出
const like = () => emit('like', props.comment);

const getAuthorName = (author) =>
    author?.class_name ? `${author.class_name} ${author.name}` : author?.name || '匿名用户';

const formatTime = (time) => dayjs(time).fromNow();
</script>

<style scoped>
.comment-node {
  padding: 12px;
  border-radius: 6px;
  transition: background-color 0.3s ease;
}

.reply-highlight {
  background-color: #ecf5ff;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.author-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  flex-grow: 1;
}

.author-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.comment-time {
  font-size: 12px;
  color: #999;
}

.comment-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.comment-content {
  margin-top: 8px;
  margin-left: 42px; /* 与头像对齐 */
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.replies-list {
  margin-top: 12px;
  margin-left: 28px;
  padding-left: 14px;
  border-left: 2px solid #e5e9f2;
}

.comment-composer-wrapper {
  margin-left: 42px;
  margin-top: 12px;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>