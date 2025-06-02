// 课程相关 API
import couRequest from '@/utils/request_cou'

// ---------- 课程管理 ----------
export const fetchCourses = (params) => couRequest.get('/courses/', { params })
export const fetchCourse = (id) => couRequest.get(`/courses/${id}/`)
export const createCourse = (data) => couRequest.post('/courses/', data)
export const updateCourse = (id, data) => couRequest.patch(`/courses/${id}/`, data)
export const deleteCourse = (id) => couRequest.delete(`/courses/${id}/`)

// ---------- 课程绑定班级 ----------
export const fetchCourseClasses = (courseId, params) => couRequest.get(`/courses/${courseId}/classes/`, { params })
export const createTeacherCourseClass = (data) => couRequest.post('/teacher-course-classes/', data)
export const updateTeacherCourseClass = (id, data) => couRequest.patch(`/teacher-course-classes/${id}/`, data)
export const deleteTeacherCourseClass = (id) => couRequest.delete(`/teacher-course-classes/${id}/`)
export const fetchCourseStudentCount = (courseId) => couRequest.get(`/courses/${courseId}/studentcount/`)


export function fetchAvailableCourses(params) {
  return couRequest({
    url: '/available-courses/',
    method: 'get',
    params
  })
}

export function fetchTeacherCourseClass(courseId) {
    return couRequest({
        url: `/teacher-course-classes/${courseId}/`,
        method: 'get'
    })
}

