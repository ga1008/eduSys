import AdminLayout from '@/layouts/AdminLayout.vue'
import AdminHome from '@/views/admin/AdminHome.vue'

export default [
    {
        path: '/admin',
        component: AdminLayout,
        meta: {requiresAuth: true, role: 'admin'},
        children: [
            {path: '', name: 'AdminHome', component: AdminHome},

            // ---------- 超级管理员管理 (新增) ----------
            {
                path: 'superadmins',
                name: 'AdminSuperAdmins',
                component: () => import('@/views/admin/superadmins/SuperAdminList.vue')
            },
            {
                path: 'superadmins/new',
                name: 'AdminSuperAdminCreate',
                component: () => import('@/views/admin/superadmins/SuperAdminForm.vue')
            },
            {
                path: 'superadmins/:id/edit',
                name: 'AdminSuperAdminEdit',
                component: () => import('@/views/admin/superadmins/SuperAdminForm.vue'),
                props: true
            },

            // ---------- 班级管理 ----------
            {path: 'classes', name: 'AdminClasses', component: () => import('@/views/admin/classes/ClassList.vue')},
            {
                path: 'classes/new',
                name: 'AdminClassCreate',
                component: () => import('@/views/admin/classes/ClassForm.vue')
            },
            {
                path: 'classes/:id/edit',
                name: 'AdminClassEdit',
                component: () => import('@/views/admin/classes/ClassForm.vue'),
                props: true
            },
            {
                path: 'classes/:id/students',
                name: 'AdminClassStudents',
                component: () => import('@/views/admin/classes/ClassStudents.vue'),
                props: route => ({classId: route.params.id})
            },

            // ----------课程管理----------
            {path: 'courses', name: 'AdminCourses', component: () => import('@/views/admin/courses/CourseList.vue')},
            {
                path: 'courses/new',
                name: 'AdminCourseCreate',
                component: () => import('@/views/admin/courses/CourseForm.vue')
            },
            {
                path: 'courses/:id/edit',
                name: 'AdminCourseEdit',
                component: () => import('@/views/admin/courses/CourseForm.vue'),
                props: true
            },
            {
                path: 'courses/:id/classes',
                name: 'AdminCourseClasses',
                component: () => import('@/views/admin/courses/CourseClasses.vue'),
                props: route => ({courseId: route.params.id})
            },

            // ---------- 教师管理 ----------
            {
                path: 'teachers',
                name: 'AdminTeachers',
                component: () => import('@/views/admin/teachers/TeacherList.vue')
            },
            {
                path: 'teachers/new',
                name: 'AdminTeacherCreate',
                component: () => import('@/views/admin/teachers/TeacherForm.vue')
            },
            {
                path: 'teachers/:id/edit',
                name: 'AdminTeacherEdit',
                component: () => import('@/views/admin/teachers/TeacherForm.vue'),
                props: true
            },
        ]
    }
]