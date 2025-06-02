// src/api/homeworks.js
import couRequest from '@/utils/request_cou'

// 作业相关 API
export const fetchHomeworks = (courseClassId, params = {}) =>
  couRequest.get('/homeworks/', {
    params: { course_class: courseClassId, ...params }
  })
export const fetchHomework = (id) => couRequest.get(`/homeworks/${id}/`)
export const createHomework = (data) => couRequest.post('/homeworks/', data)
export const updateHomework = (id, data) => couRequest.patch(`/homeworks/${id}/`, data)
export const deleteHomework = (id) => couRequest.delete(`/homeworks/${id}/`)

// 提交列表
export const fetchHomeworkSubmissions = (homeworkId, params = {}) =>
  couRequest.get(`/homeworks/${homeworkId}/submissions/`, { params })

// 批改
export const gradeSubmission = (submissionId, data) =>
  couRequest.patch(`/homeworks/submissions/${submissionId}/grade/`, data)