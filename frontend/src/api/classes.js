// 班级与学生相关 API
import request from '@/utils/request'

// ---------- 班级 ----------
export const fetchClasses = (params) => request.get('/classes/', { params })
export const createClass  = (data)   => request.post('/classes/', data)
export const updateClass  = (id,d)   => request.put(`/classes/${id}/`, d)
export const deleteClass  = (id)     => request.delete(`/classes/${id}/`)
export const fetchClass   = (id)     => request.get(`/classes/${id}/`)

// ---------- 班级学生 ----------
export const fetchStudents      = (classId, params) => request.get(`/classes/${classId}/students/`, { params })
export const importStudents     = (classId, fd)     =>
  request.post(`/classes/${classId}/import-students/`, fd, { headers:{'Content-Type':'multipart/form-data'} })
export const clearStudents      = (classId)         => request.delete(`/classes/${classId}/students/`)
export const downloadTpl        = () => request.get('/students/download_template/', { responseType:'blob' })
export const fetchStudentsCount = (classId) => request.get(`/classes/${classId}/students-count/`)

// ---------- 单个学生 ----------
export const createStudent = (data)   => request.post('/students/', data)
export const updateStudent = (id,d)   => request.put(`/students/${id}/`, d)
export const deleteStudent = (id)     => request.delete(`/students/${id}/`)
