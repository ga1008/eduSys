import axios from 'axios';
import {useUserStore} from '@/store/user';
import router from '@/router';

// 创建一个专门用于 forum API 的 axios 实例
const forumService = axios.create({
    baseURL: '/forum/api', // 指向我们在 vite.config.js 中为论坛设置的代理
    timeout: 10000,
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
});

// 响应拦截器，处理401未授权的情况
forumService.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err.response?.status === 401) {
            useUserStore().logout();
            router.push('/login/student');
        }
        return Promise.reject(err);
    }
);

// --- 帖子 (Post) 相关 API ---

/**
 * 获取帖子列表
 * @param {object} params - 查询参数, e.g., { page: 1, search: '关键词', tags__name: 'tag', ordering: '-like_count' }
 */
export const fetchPosts = (params) => forumService.get('/posts/', {params});

/**
 * 获取单个帖子的详细信息
 * @param {number} postId - 帖子ID
 */
export const fetchPostById = (postId) => forumService.get(`/posts/${postId}/`);

/**
 * 创建新帖子
 * @param {object} formData - FormData object
 */
export const createPost = (formData) => forumService.post('/posts/', formData, {
    headers: {
        'Content-Type': 'multipart/form-data',
    },
});

/**
 * 更新帖子
 * @param {number} postId - 帖子ID
 * @param {object} postData - 需要更新的数据
 */
export const updatePost = (postId, postData) => forumService.patch(`/posts/${postId}/`, postData);

/**
 * 删除帖子
 * @param {number} postId - 帖子ID
 */
export const deletePost = (postId) => forumService.delete(`/posts/${postId}/`);

/**
 * 点赞帖子
 * @param {number} postId - 帖子ID
 */
export const likePost = (postId) => forumService.post(`/posts/${postId}/like/`);

/**
 * 取消点赞帖子
 * @param {number} postId - 帖子ID
 */
export const unlikePost = (postId) => forumService.post(`/posts/${postId}/unlike/`);

/**
 * 获取热门帖子
 * @param {string} period - 'week' or 'month'
 */
export const fetchHotPosts = (period = 'week') => forumService.get('/posts/hot/', {params: {period}});


// --- 评论 (Comment) 相关 API ---

/**
 * 获取某个帖子的评论列表
 * @param {number} postId - 帖子ID
 */
export const fetchComments = (postId) => forumService.get(`/posts/${postId}/comments/`);

/**
 * 发表评论
 * @param {number} postId - 帖子ID
 * @param {object} commentData - { content, is_anonymous, parent_comment }
 */
export const createComment = (postId, commentData) => forumService.post(`/posts/${postId}/comments/`, commentData);


/**
 * 【新增】点赞评论
 * @param {number} postId - 帖子ID
 * @param {number} commentId - 评论ID
 */
export const likeComment = (postId, commentId) => forumService.post(`/posts/${postId}/comments/${commentId}/like/`);

/**
 * 【新增】取消点赞评论
 * @param {number} postId - 帖子ID
 * @param {number} commentId - 评论ID
 */
export const unlikeComment = (postId, commentId) => forumService.post(`/posts/${postId}/comments/${commentId}/unlike/`);


/**
 * 删除评论
 * @param {number} postId - 帖子ID
 * @param {number} commentId - 评论ID
 */
export const deleteComment = (postId, commentId) => forumService.delete(`/posts/${postId}/comments/${commentId}/`);


// --- 标签 (Tag) 相关 API ---

/**
 * 获取所有标签
 */
export const fetchTags = () => forumService.get('/tags/');

export default forumService;