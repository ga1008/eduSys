// 教师角色路由配置
import TeacherLayout from '@/layouts/TeacherLayout.vue'

export default [
    {
        path: '/teacher',
        component: TeacherLayout,
        meta: {requiresAuth: true, role: 'teacher'},
        children: [
            {
                path: '',
                redirect: '/teacher/dashboard',
            },
            {
                path: 'dashboard',
                name: 'TeacherDashboard',
                component: () => import('@/views/teacher/Dashboard.vue'),
                meta: {title: '教师首页'}
            },
            // 课程管理相关路由
            {
                path: 'courses',
                name: 'TeacherCourses',
                component: () => import('@/views/teacher/courses/CourseClassList.vue'),
                meta: {title: '我的课程'}
            },
            {
                path: 'courses/edit/:id',
                name: 'TeacherCourseEdit',
                component: () => import('@/views/teacher/courses/CourseClassForm.vue'),
                meta: {title: '设置课程'}
            },
            {
                path: 'courses/progress/:id',
                name: 'TeacherCourseProgress',
                component: () => import('@/views/teacher/courses/CourseProgress.vue'),
                meta: {title: '课程进度管理'}
            },
            {
                path: 'students',  // 新增：从菜单直接进入的路由
                name: 'TeacherStudents',
                component: () => import('@/views/teacher/courses/CourseStudents.vue'),
                meta: {title: '我的学生'}
            },
            {
                path: 'courses/students/:id',
                name: 'TeacherCourseStudents',
                component: () => import('@/views/teacher/courses/CourseStudents.vue'),
                meta: {title: '学生名单'}
            },
            // 作业管理相关路由
            {
                path: 'courses/homeworks/:id/create',         // 新建
                name: 'TeacherCourseHomeworkCreate',
                component: () => import('@/views/teacher/homework/HomeworkForm.vue'),
                meta: {title: '新建作业'}
            },
            {
                path: 'courses/homeworks/:id/edit/:homeworkId', // 编辑
                name: 'TeacherCourseHomeworkEdit',
                component: () => import('@/views/teacher/homework/HomeworkForm.vue'),
                meta: {title: '编辑作业'}
            },
            {
                path: 'courses/homeworks/:id?',               // 列表 (可缺 id)
                name: 'TeacherCourseHomeworks',
                component: () => import('@/views/teacher/homework/HomeworkList.vue'),
                meta: {title: '作业列表'}
            },
            {
                path: 'courses/import',
                name: 'TeacherCourseImport',
                component: () => import('@/views/teacher/courses/CourseImport.vue'),
                meta: {title: '导入课程'}
            },
            {
                path: 'courses/create',
                name: 'TeacherCourseCreate',
                component: () => import('@/views/teacher/courses/CourseClassCreate.vue'),
                meta: {title: '新建课程班级', adminOnly: true}
            },
            {
                path: 'homeworks/:hwId/submissions',
                name: 'TeacherHomeworkSubmissions',
                component: () => import('@/views/teacher/homework/HomeworkSubmissionList.vue'),
                meta: {title: '学生提交'}
            },
            {
                path: 'homeworks/submissions/:subId/grade',
                name: 'TeacherHomeworkGrade',
                component: () => import('@/views/teacher/homework/HomeworkGrade.vue'),
                props: true,
                meta: {title: '批改作业'}
            },
            {
                path: 'courses/:courseClassId/students/:studentId',
                name: 'CourseStudentDetail',
                component: () => import('@/views/teacher/courses/CourseStudentDetail.vue'),
                meta: {title: '学生详情'}
            },
            {
                path: 'messages',
                component: () => import('@/views/teacher/messages/MessageCenter.vue'),
                redirect: '/teacher/messages/inbox',
                children: [
                    {
                        path: 'inbox',
                        name: 'TeacherMessageInbox',
                        component: () => import('@/views/teacher/messages/Inbox.vue'),
                        meta: {title: '收件箱'}
                    },
                    {
                        path: 'view/:id',
                        name: 'TeacherMessageView',
                        component: () => import('@/views/teacher/messages/MessageView.vue'),
                        props: true,
                        meta: {title: '查看消息'}
                    },
                    {
                        path: 'compose',
                        name: 'TeacherMessageCompose',
                        component: () => import('@/views/teacher/messages/Compose.vue'),
                        meta: {title: '写消息'}
                    },
                    {
                        path: 'settings',
                        name: 'TeacherMessageSettings',
                        component: () => import('@/views/teacher/messages/Settings.vue'),
                        meta: {title: '消息设置'}
                    }
                ]
            },
        ]
    }
]