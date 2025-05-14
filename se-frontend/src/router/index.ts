import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useUserStore } from '@/stores/user';

/* ---------------- 路由表 ---------------- */
const routes: RouteRecordRaw[] = [
    { path: '/', redirect: '/login' },

    /* === 认证相关 === */
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/login/LoginView.vue'),
        meta: { requiresAuth: false },
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('@/views/login/RegisterView.vue'),
        meta: { requiresAuth: false },
    },
    {
        path: '/reset-password',
        name: 'ResetPassword',
        component: () => import('@/views/login/ResetPasswordView.vue'),
        meta: { requiresAuth: false },
    },

    /* === 学生端 === */
    {
        path: '/student/home',
        name: 'StudentHome',
        component: () => import('@/views/student/StudentHomeView.vue'),
        meta: { requiresAuth: true, role: 'student' },
    },
    {
        path: '/student/course/:id',
        name: 'StudentCourse',
        component: () => import('@/views/student/StudentCourseView.vue'),
        meta: { requiresAuth: true, role: 'student' },
    },
    {
        path: '/student/course/:id/assignment/:assignmentId',
        name: 'StudentAssignment',
        component: () => import('@/views/student/StudentAssignmentView.vue'),
        meta: { requiresAuth: true, role: 'student' },
    },

    /* === 教师端 === */
    {
        path: '/teacher/home',
        name: 'TeacherHome',
        component: () => import('@/views/teacher/TeacherHomeView.vue'),
        meta: { requiresAuth: true, role: 'teacher' },
    },
    {
        path: '/teacher/course/:id',
        name: 'TeacherCourse',
        component: () => import('@/views/teacher/TeacherCourseView.vue'),
        meta: { requiresAuth: true, role: 'teacher' },
    },
    {
        path: '/teacher/course/:id/assignment/:assignmentId',
        name: 'TeacherAssignment',
        component: () => import('@/views/teacher/TeacherAssignmentView.vue'),
        meta: { requiresAuth: true, role: 'teacher' },
    },

    /* === LLM 交互（公共） === */
    {
        path: '/llm',
        name: 'LLMIndex',
        component: () => import('@/views/llm/index.vue'),
        meta: { requiresAuth: true },
    },
    {
        path: '/llm/chat/:id',
        name: 'ChatPage',
        component: () => import('@/views/llm/chat/ChatPage.vue'),
        meta: { requiresAuth: true },
    },
    {
        path: '/llm/agent/:id',
        name: 'AgentPage',
        component: () => import('@/views/llm/agent/AgentPage.vue'),
        meta: { requiresAuth: true },
    },

    /* === 兜底 404 === */
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/common/NotFound.vue'),
    },
];

/* ---------------- 实例化 ---------------- */
const router = createRouter({
    history: createWebHistory(),
    routes,
});

/* ---------------- 全局守卫 ---------------- */
router.beforeEach((to, _from, next) => {
    const store = useUserStore();

    // 1. 需要登录但未认证
    if (to.meta.requiresAuth && !store.isAuthenticated) {
        return next('/login');
    }

    // 2. 角色不匹配
    if (to.meta.role && store.role && to.meta.role !== store.role) {
        return next(store.role === 'teacher' ? '/teacher/home' : '/student/home');
    }

    next();
});

export default router;