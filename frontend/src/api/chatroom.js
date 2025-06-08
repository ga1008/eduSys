import request from '@/utils/request_cou'; // 假设聊天室 API 走 course 代理

// 获取聊天室历史消息
export const fetchChatHistory = (roomId, params) => {
    return request.get(`/chat/api/chatrooms/${roomId}/messages/`, {params});
};

// 获取聊天室成员列表
export const fetchChatMembers = (roomId) => {
    return request.get(`/chat/api/chatrooms/${roomId}/members/`);
};

// 上传文件到聊天室
export const uploadChatFile = (roomId, formData) => {
    return request.post(`/chat/api/chatrooms/${roomId}/upload/`, formData, {
        headers: {'Content-Type': 'multipart/form-data'}
    });
};

// 修改自己的昵称
export const updateMyNickname = (roomId, nickname) => {
    return request.patch(`/chat/api/chatrooms/${roomId}/me/`, {nickname});
};