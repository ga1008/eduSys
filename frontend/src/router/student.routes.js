import StudentLayout from '@/layouts/StudentLayout.vue'
import StudentHome from '@/views/student/StudentHome.vue'

export default [
  {
    path: '/student',
    component: StudentLayout,
    meta: { requiresAuth: true, role: 'student' },
    children: [
      // 主页
      {
        path: '',
        redirect: '/student/assignments'
      },

      // 大屏
      {
        path: 'dashboard',
        name: 'StudentDashboard',
        component: () => import('@/views/student/Dashboard.vue'),
        meta: { title: '大屏' }
      },

      // 我的课程
      {
        path: 'courses',
        name: 'StudentCourses',
        component: () => import('@/views/student/CourseList.vue'),
        meta: { title: '我的课程' }
      },

      // 🔥 **新增：我的作业（无课程 id）**
      {
        path: 'assignments',
        name: 'StudentAssignments',
        component: () => import('@/views/student/AssignmentList.vue'),
        meta: { title: '我的作业' }
      },

      // 课程详情
      {
        path: 'courses/:id?',
        name: 'StudentCourseDetail',
        component: () => import('@/views/student/CourseDetail.vue'),
        meta: { title: '课程详情' },
        children: [
          {
            path: 'assignments',
            name: 'StudentCourseAssignments',
            component: () => import('@/views/student/AssignmentList.vue'),
            meta: { title: '作业列表' }
          },
          {
            path: 'materials',
            name: 'StudentCourseMaterials',
            component: () => import('@/views/student/MaterialList.vue'),
            meta: { title: '学习资料' }
          }
        ]
      },

      // 作业提交
      {
        path: 'assignments/:id/submit',
        name: 'StudentAssignmentSubmit',
        component: () => import('@/views/student/AssignmentSubmit.vue'),
        props: true,
        meta: { title: '提交作业' }
      },

      // 通知公告
      {
        path: 'notices',
        name: 'StudentNotices',
        component: () => import('@/views/student/NoticeList.vue'),
        meta: { title: '通知公告' }
      }
    ]
  }
]