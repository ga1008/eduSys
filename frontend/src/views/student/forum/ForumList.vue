<template>
  <div class="forum-list-page">
    <el-row :gutter="20">
      <!-- 主内容区：帖子列表 -->
      <el-col :xs="24" :md="16">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>最新帖子</span>
              <el-button type="primary" :icon="Edit" @click="showPostDialog = true">发布新帖</el-button>
            </div>
          </template>

          <div v-loading="loadingPosts">
            <div v-if="posts.length === 0" class="empty-state">
              <el-empty description="还没有人发帖，快来抢占沙发吧！"/>
            </div>
            <div v-else>
              <div v-for="post in posts" :key="post.id" class="post-item" @click="goToPost(post.id)">
                <div class="post-author-info">
                  <el-avatar :size="30" :src="post.author.avatar || defaultAvatar"/>
                  <span class="author-name">{{ post.author.real_name || '匿名用户' }}</span>
                </div>
                <h3 class="post-title">{{ post.title }}</h3>
                <div class="post-meta">
                  <el-tag v-for="tag in post.tags" :key="tag.id" size="small" type="success" effect="plain">{{
                      tag.name
                    }}
                  </el-tag>
                  <span class="meta-item"><el-icon><View/></el-icon>{{ post.view_count }}</span>
                  <span class="meta-item"><el-icon><StarFilled/></el-icon>{{ post.like_count }}</span>
                  <span class="meta-item"><el-icon><ChatDotRound/></el-icon>{{ post.comment_count }}</span>
                  <span class="meta-item-time">{{ formatTime(post.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

        </el-card>
      </el-col>

      <!-- 侧边栏：热点帖子和标签 -->
      <el-col :xs="24" :md="8">
        <el-card class="box-card hot-posts-card">
          <template #header>
            <div class="card-header"><span>热门动态</span></div>
          </template>
          <el-tabs v-model="hotPostPeriod" @tab-click="fetchHotPostsData">
            <el-tab-pane label="本周热门" name="week"></el-tab-pane>
            <el-tab-pane label="本月热门" name="month"></el-tab-pane>
          </el-tabs>
          <div v-loading="loadingHotPosts">
            <div v-for="(post, index) in hotPosts" :key="post.id" class="hot-post-item" @click="goToPost(post.id)">
              <span class="hot-rank" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
              <span class="hot-title">{{ post.title }}</span>
            </div>
            <el-empty v-if="hotPosts.length === 0" description="暂无热门" :image-size="50"/>
          </div>
        </el-card>

        <el-card class="box-card tags-card">
          <template #header>
            <div class="card-header"><span>热门标签</span></div>
          </template>
          <div class="tag-cloud">
            <el-tag v-for="tag in tags" :key="tag.id" class="tag-item" effect="light" round>
              {{ tag.name }}
            </el-tag>
          </div>
          <el-empty v-if="tags.length === 0" description="暂无标签" :image-size="50"/>
        </el-card>
      </el-col>
    </el-row>

    <!-- 发布新帖弹窗 -->
    <el-dialog v-model="showPostDialog" title="发布新帖" width="60%" :close-on-click-modal="false">
      <el-form :model="newPostForm" label-width="100px" ref="postFormRef">
        <el-form-item label="标题" prop="title" required>
          <el-input v-model="newPostForm.title" placeholder="一个引人注目的标题"/>
        </el-form-item>
        <el-form-item label="内容" prop="content" required>
          <v-md-editor
              v-model="newPostForm.content"
              height="300px"
              placeholder="分享你的想法，支持Markdown，可拖拽上传图片及附件..."
          ></v-md-editor>
        </el-form-item>
        <el-form-item label="附件">
          <el-upload
              v-model:file-list="newPostForm.files"
              action="#"
              :auto-upload="false"
              multiple
              drag>
            <el-icon class="el-icon--upload">
              <upload-filled/>
            </el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          </el-upload>
        </el-form-item>
        <el-form-item label="发帖身份">
          <el-switch v-model="newPostForm.is_anonymous" active-text="匿名发布" inactive-text="实名发布"/>
        </el-form-item>
        <el-form-item label="评论设置">
          <el-checkbox v-model="newPostForm.allow_comments" label="允许他人评论"/>
          <el-checkbox v-model="newPostForm.allow_ai_comments" label="允许 AI 助教参与讨论"/>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPostDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreatePost" :loading="creatingPost">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {useRouter} from 'vue-router';
import {ElMessage,} from 'element-plus';
import '@kangc/v-md-editor';
import {createPost, fetchHotPosts, fetchPosts, fetchTags} from '@/api/forum';
import {ChatDotRound, Edit, StarFilled, View} from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const router = useRouter();

// 数据状态
const posts = ref([]);
const hotPosts = ref([]);
const tags = ref([]);
const loadingPosts = ref(false);
const loadingHotPosts = ref(false);
const hotPostPeriod = ref('week');
const showPostDialog = ref(false);
const creatingPost = ref(false);
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png';

const newPostForm = ref({
  title: '',
  content: '',
  is_anonymous: true,
  allow_comments: true,
  allow_ai_comments: false,
});

// 获取数据方法
const fetchData = async () => {
  loadingPosts.value = true;
  try {
    const res = await fetchPosts();
    posts.value = res.data;
  } catch (error) {
    ElMessage.error('加载帖子列表失败');
  } finally {
    loadingPosts.value = false;
  }
};

const fetchHotPostsData = async () => {
  loadingHotPosts.value = true;
  try {
    const res = await fetchHotPosts(hotPostPeriod.value);
    hotPosts.value = res.data;
  } catch (error) {
    ElMessage.error('加载热门帖子失败');
  } finally {
    loadingHotPosts.value = false;
  }
};

const fetchTagsData = async () => {
  try {
    const res = await fetchTags();
    tags.value = res.data;
  } catch (error) {
    console.error('加载标签失败', error);
  }
};

// 事件处理
const goToPost = (postId) => {
  router.push({name: 'StudentPostDetail', params: {postId}});
};

const handleCreatePost = async () => {
  if (!newPostForm.value.title || !newPostForm.value.content) {
    ElMessage.warning('标题和内容不能为空！');
    return;
  }
  // ... 校验逻辑 ...
  const formData = new FormData();
  formData.append('title', newPostForm.value.title);
  formData.append('content', newPostForm.value.content); // Markdown内容
  formData.append('is_anonymous', newPostForm.value.is_anonymous);
  // ... 其他表单字段 ...

  // 添加文件
  newPostForm.value.files.forEach(file => {
    formData.append('files', file.raw); // 添加原始文件对象
  });

  creatingPost.value = true;
  try {
    await createPost(newPostForm.value);
    ElMessage.success('发布成功！');
    showPostDialog.value = false;
    newPostForm.value = {title: '', content: '', is_anonymous: true, allow_comments: true, allow_ai_comments: false};
    fetchData(); // 重新加载列表
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发布失败，请稍后再试');
  } finally {
    creatingPost.value = false;
  }
};

// 格式化时间
const formatTime = (time) => dayjs(time).fromNow();

// 初始化加载
onMounted(() => {
  fetchData();
  fetchHotPostsData();
  fetchTagsData();
});
</script>

<style scoped>
/* 样式参考知乎和Quora，但更简洁 */
.forum-list-page {
  padding: 10px;
}

.box-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
  font-weight: bold;
}

.post-item {
  padding: 15px 0;
  border-bottom: 1px solid #e8e8e8;
  cursor: pointer;
  transition: background-color 0.2s;
}

.post-item:hover {
  background-color: #f7f7f7;
}

.post-item:last-child {
  border-bottom: none;
}

.post-author-info {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.9rem;
  color: #555;
}

.author-name {
  margin-left: 8px;
}

.post-title {
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0 0 10px 0;
  color: #1a1a1a;
}

.post-meta {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 0.85rem;
  color: #8590a6;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.meta-item-time {
  margin-left: auto;
}

.hot-posts-card .el-tabs__header {
  margin-bottom: 10px;
}

.hot-post-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  cursor: pointer;
  font-size: 0.95rem;
}

.hot-post-item:hover .hot-title {
  color: #409EFF;
}

.hot-rank {
  font-weight: bold;
  font-style: italic;
  margin-right: 10px;
  width: 20px;
  text-align: center;
}

.rank-1 {
  color: #fe2d46;
}

.rank-2 {
  color: #ff6526;
}

.rank-3 {
  color: #ff9a0e;
}

.hot-title {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tags-card .tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  cursor: pointer;
}
</style>
