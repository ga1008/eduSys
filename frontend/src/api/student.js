import stuRequest from '@/utils/request_stu'
import couRequest from '@/utils/request_cou'

export const fetchStudentCourses = () => stuRequest.get('/courses/')
export const fetchCourseAssignments = (courseId) =>
    stuRequest.get(`/courses/${courseId}/assignments/`)
export const submitAssignment = (assignmentId, data) =>
    stuRequest.post(`/assignments/${assignmentId}/submissions/`, data)

export const fetchStudentDashboard = () => stuRequest.get('/dashboard/')
export const fetchStudentNotices = () => stuRequest.get('/notices/')

export const fetchStudentCourseDetail = (courseId) =>
    stuRequest.get(`/courses/${courseId}/`)

export const deleteDrawSubmission = (submissionId) =>
    stuRequest.delete(`/assignments/submissions/${submissionId}/`)

// 修改为stuRequest
export const submitAssignmentWithFiles = (assignmentId, formData) =>
    stuRequest.post(`/assignments/${assignmentId}/submissions/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

// 获取课程材料列表
export const fetchCourseMaterials = (courseId, params) =>
    stuRequest.get(`/courses/${courseId}/materials/`, { params })

// 下载课程材料 (这里保留couRequest，因为可能是公共API)
export const downloadCourseMaterial = (materialId) =>
    couRequest.get(`/materials/${materialId}/download/`, { responseType: 'blob' })

/** 获取「作业本身」信息 */
export const fetchAssignmentInfo = (assignmentId) =>
  stuRequest.get(`/assignments/${assignmentId}/assignment_info`)

/** 获取「我对该作业的提交记录」；404 = 尚未提交 */
export const fetchMySubmission = (assignmentId) =>
  stuRequest.get(`/assignments/${assignmentId}/submissions/me/`)

export const updateSubmission = (submissionId, formData) =>
  stuRequest.patch(`/assignments/submissions/${submissionId}/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
