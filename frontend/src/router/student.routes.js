// frontend/src/router/student.routes.js
import StudentLayout from '@/layouts/StudentLayout.vue'

export default [
  {
    path: '/student',
    component: StudentLayout,
    meta: { requiresAuth: true, role: 'student' },
    children: [
      {
        path: '', // 学生模块的默认路径
        name: 'StudentHome', // 定义为学生首页
        component: () => import('@/views/student/StudentHome.vue'), // 指向您重新设计的StudentHome.vue
        meta: { title: '我的主页' }
      },
      {
        path: 'courses',
        name: 'StudentCourses',
        component: () => import('@/views/student/CourseList.vue'),
        meta: { title: '我的课程' }
      },
      {
        path: 'assignments', // 查看所有作业的列表页面
        name: 'StudentAllAssignments',
        component: () => import('@/views/student/AssignmentList.vue'),
        meta: { title: '全部作业' }
      },
      // 其他学生子路由...
       {
        path: 'courses/:id', // 课程详情页，:id 为 TeacherCourseClass 的 ID
        name: 'StudentCourseDetail',
        component: () => import('@/views/student/CourseDetail.vue'),
        props: true,
        meta: { title: '课程详情' },
        // ... 可能的子路由，如课程内的作业、资料列表
      },
      {
        path: 'assignments/:id/submit', // 作业提交/查看页面，:id 为 Assignment 的 ID
        name: 'StudentAssignmentSubmit',
        component: () => import('@/views/student/AssignmentSubmit.vue'),
        props: true,
        meta: { title: '作业详情与提交' }
      },
      {
        path: 'notices',
        name: 'StudentNotices',
        component: () => import('@/views/student/NoticeList.vue'), // 假设您有此组件
        meta: { title: '通知公告' }
      }
    ]
  }
]