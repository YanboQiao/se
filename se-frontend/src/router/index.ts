import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useUserStore } from '@/stores/user';

/* 路由表 */
const routes: Array<RouteRecordRaw> = [
    { path: '/', redirect: '/login' },

    // 登录页
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/login/LoginView.vue'),
        meta: { requiresAuth: false },
    },

    // 学生主页
    {
        path: '/student/home',
        name: 'StudentHome',
        component: () => import('@/views/student/StudentHomeView.vue'),
        meta: { requiresAuth: true, role: 'student' },
    },

    // 教师主页
    {
        path: '/teacher/home',
        name: 'TeacherHome',
        component: () => import('@/views/teacher/TeacherHomeView.vue'),
        meta: { requiresAuth: true, role: 'teacher' },
    },

    // 重置密码
    {
        path: '/reset-password',
        name: 'ResetPassword',
        component: () => import('@/views/login/ResetPasswordView.vue'),
        meta: { requiresAuth: false },
    },
];

/* 实例化 */
const router = createRouter({
    history: createWebHistory(),
    routes,
});

/* 全局守卫 */
router.beforeEach((to, _from, next) => {
    const store = useUserStore();

    // 需要登录但未认证 → 重定向登录页
    if (to.meta.requiresAuth && !store.isAuthenticated) {
        return next('/login');
    }

    // 已登录但角色不匹配 → 重定向各自主页
    if (to.meta.role && store.role && to.meta.role !== store.role) {
        return next(store.role === 'teacher' ? '/teacher/home' : '/student/home');
    }

    next();
});

export default router;