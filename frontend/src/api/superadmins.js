// API calls for superadmin management
import request from '@/utils/request'; // 使用基础 request 实例

export const fetchSuperAdmins = (params) => request.get('/superadmins/', {params});

export const fetchSuperAdmin = (id) => request.get(`/superadmins/${id}/`);

export const createSuperAdmin = (data) => request.post('/superadmins/', data);

export const updateSuperAdmin = (id, data) => request.patch(`/superadmins/${id}/`, data);

export const deleteSuperAdmin = (id) => request.delete(`/superadmins/${id}/`);