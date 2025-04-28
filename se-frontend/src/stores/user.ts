import {defineStore} from 'pinia';
import axios from 'axios';

interface LoginPayload {
    username: string;
    password: string;
    role: 'student' | 'teacher';
}

interface ResetPayload {
    username: string;
    newPassword: string;
}

interface UserState {
    token: string | null;
    username: string | null;
    role: 'student' | 'teacher' | null;
}

export const useUserStore = defineStore('user', {
    state: (): UserState => ({
        token: localStorage.getItem('token'),
        username: localStorage.getItem('username'),
        role: localStorage.getItem('role') as 'student' | 'teacher' | null,
    }),

    getters: {
        isAuthenticated: (state) => Boolean(state.token),
    },

    actions: {
        /** 登录（教师 / 学生） */
        async login({username, password, role}: LoginPayload) {
            // 👉 请替换为真实后端接口
            const {data} = await axios.post('/api/login', {username, password, role});

            this.token = data.token;
            this.username = username;
            this.role = role;

            localStorage.setItem('token', this.token!);
            localStorage.setItem('username', this.username!);
            localStorage.setItem('role', this.role);
        },

        /** 重置密码 */
        async resetPassword({username, newPassword}: ResetPayload) {
            // 👉 请替换为真实后端接口
            await axios.post('/api/reset-password', {username, newPassword});
        },

        /** 退出登录 */
        logout() {
            this.token = null;
            this.username = null;
            this.role = null;
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            localStorage.removeItem('role');
        },
    },
});
