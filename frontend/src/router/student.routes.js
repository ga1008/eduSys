// frontend/src/router/student.routes.js
import StudentLayout from '@/layouts/StudentLayout.vue'

export default [
    {
        path: '/student',
        component: StudentLayout,
        meta: {requiresAuth: true, role: 'student'},
        children: [
            {
                path: '', // 学生模块的默认路径
                name: 'StudentHome', // 定义为学生首页
                component: () => import('@/views/student/StudentHome.vue'), // 指向您重新设计的StudentHome.vue
                meta: {title: '我的主页'}
            },
            {
                path: 'courses',
                name: 'StudentCourses',
                component: () => import('@/views/student/CourseList.vue'),
                meta: {title: '我的课程'}
            },
            {
                path: 'assignments', // 查看所有作业的列表页面
                name: 'StudentAllAssignments',
                component: () => import('@/views/student/AssignmentList.vue'),
                meta: {title: '全部作业'}
            },
            // 其他学生子路由...
            {
                path: 'courses/:id', // 课程详情页，:id 为 TeacherCourseClass 的 ID
                name: 'StudentCourseDetail',
                component: () => import('@/views/student/CourseDetail.vue'),
                props: true,
                meta: {title: '课程详情'},
                children: [
                    {
                        path: '', // 默认显示课程信息，通过 tab 控制
                        redirect: to => ({name: 'StudentCourseDetail', params: to.params, query: {tab: 'info'}}) // 可选：或不设重定向，由 tab 默认值控制
                    },
                    {
                        path: 'assignments',
                        name: 'StudentCourseAssignments', // 用于 <router-view name="StudentCourseAssignmentsView">
                        component: () => import('@/views/student/AssignmentList.vue'), // 假设是这个组件
                        meta: {title: '课程作业'}
                    },
                    {
                        path: 'materials',
                        name: 'StudentCourseMaterials', // 用于 <router-view name="StudentCourseMaterialsView">
                        component: () => import('@/views/student/MaterialList.vue'), // 假设是这个组件
                        meta: {title: '学习资料'}
                    }
                ]
            },
            {
                path: 'assignments/:id/submit', // 作业提交/查看页面，:id 为 Assignment 的 ID
                name: 'StudentAssignmentSubmit',
                component: () => import('@/views/student/AssignmentSubmit.vue'),
                props: true,
                meta: {title: '作业详情与提交'}
            },
            {
                path: 'notices',
                name: 'StudentNotices',
                component: () => import('@/views/student/NoticeList.vue'), // 假设您有此组件
                meta: {title: '通知公告'}
            },
            // --- 新增的学生消息中心路由 ---
            {
                path: 'messages',
                component: () => import('@/views/student/messages/MessageCenter.vue'),
                redirect: '/student/messages/inbox', // 默认重定向到收件箱
                children: [
                    {
                        path: 'inbox',
                        name: 'StudentMessageInbox',
                        component: () => import('@/views/student/messages/Inbox.vue'),
                        meta: {title: '收件箱'}
                    },
                    {
                        path: 'sent',
                        name: 'StudentMessageSent',
                        component: () => import('@/views/student/messages/Sent.vue'),
                        meta: {title: '已发送'}
                    },
                    {
                        path: 'view/:id',
                        name: 'StudentMessageView',
                        component: () => import('@/views/student/messages/MessageView.vue'),
                        props: true,
                        meta: {title: '查看消息'}
                    },
                    {
                        path: 'compose',
                        name: 'StudentMessageCompose',
                        component: () => import('@/views/student/messages/Compose.vue'),
                        meta: {title: '写消息'}
                    },
                    {
                        path: 'settings',
                        name: 'StudentMessageSettings',
                        component: () => import('@/views/student/messages/Settings.vue'),
                        meta: {title: '消息设置'}
                    }
                ]
            },

            // --- 新增论坛相关路由 ---
            {
                path: 'forum',
                name: 'StudentForum',
                component: () => import('@/views/student/forum/ForumList.vue'), // 论坛列表页
                meta: {title: '校园论坛'}
            },
            {
                path: 'forum/post/:postId', // 帖子详情页
                name: 'StudentPostDetail',
                component: () => import('@/views/student/forum/PostDetail.vue'), // 帖子详情页组件
                props: true,
                meta: {title: '帖子详情'}
            },
        ]
    }
]