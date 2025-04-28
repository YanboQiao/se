import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router';
import {useUserStore} from '@/stores/user';

/* 路由表 */
const routes: Array<RouteRecordRaw> = [
    {path: '/', redirect: '/login'},
    {path: '/login', name: 'Login', component: () => import('../views/login/LoginView.vue'), meta: {requiresAuth: false}},
    {path: '/home', name: 'Home', component: () => import('../views/home/HomeView.vue'), meta: {requiresAuth: true}},
    {
        path: '/reset-password',
        name: 'ResetPassword',
        component: () => import('../views/login/ResetPasswordView.vue'),
        meta: {requiresAuth: false}
    },
];

/* 实例化 */
const router = createRouter({
    history: createWebHistory(),
    routes,
});

/* 全局守卫 */
router.beforeEach((to, _from, next) => {
    const userStore = useUserStore();
    if (to.meta.requiresAuth && !userStore.isAuthenticated) {
        next('/login');
    } else {
        next();
    }
});

export default router;
