import request from '@/utils/request_cou'; // 使用 cou 代理，指向后端 8000 端口

// --- 通用接口 ---
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


// --- 管理员专用接口 ---
// 更新聊天室设置 (如禁言)
export const updateRoomSettings = (roomId, settings) => {
    return request.patch(`/chat/api/chatrooms-admin/${roomId}/`, settings);
}

// 修改成员角色
export const setMemberRole = (roomId, memberId, role) => {
    return request.post(`/chat/api/chatrooms-admin/${roomId}/members/${memberId}/role/`, {role});
}

// 踢出成员
export const kickMember = (roomId, memberId) => {
    return request.post(`/chat/api/chatrooms-admin/${roomId}/members/${memberId}/kick/`);
}

// 管理员删除消息
export const deleteMessageByAdmin = (roomId, messageId) => {
    return request.delete(`/chat/api/chatrooms-admin/${roomId}/messages/${messageId}/`);
}

// 管理员修改成员昵称
export const updateMemberNicknameByAdmin = (roomId, memberId, nickname) => {
    // 假设后端提供了一个修改成员信息的接口
    // 如果没有，此接口需要后端支持
    return request.patch(`/chat/api/chatrooms-admin/${roomId}/members/${memberId}/`, {nickname});
}