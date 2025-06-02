// 老师相关API

import request from '@/utils/request'
import couRequest from '@/utils/request_cou'

// ---------- 老师 ----------
export const fetchTeachers = (params) => request.get('/teachers/', { params })
export const fetchTeacher = (id) => request.get(`/teachers/${id}/`)
export const createTeacher = (data) => request.post('/teachers/', data)
export const updateTeacher = (id, data) => request.patch(`/teachers/${id}/`, data)
export const deleteTeacher = (id) => request.delete(`/teachers/${id}/`)

// 获取教师仪表板数据
export function fetchTeacherDashboard() {
  return couRequest({
    url: '/teacher-course-classes/dashboard/',
    method: 'get'
  })
}

// 获取教师的课程班级列表
export function fetchTeacherCourseClasses() {
  return couRequest({
    url: '/teacher-course-classes/courses/',
    method: 'get'
  })
}

export function fetchTeacherCourseClass(courseClassId) {
  return couRequest({
    url: `/teacher-course-classes/${courseClassId}/`,
    method: 'get'
  })
}

export function fetchTeacherCourseClassStudents(courseClassId) {
  return couRequest({
    url: `/teacher-course-classes/${courseClassId}/students/`,
    method: 'get'
  })
}

export function fetchUngradedHomeworks() {
  return couRequest({
    url: `/homeworks/ungraded`,
    method: 'get'
  })
}
