import {defineStore} from 'pinia';
import axios from 'axios';

interface LoginPayload {
    useremail: string;
    password: string;
    role: 'student' | 'teacher';
}

interface RegisterPayload {
    useremail: string;
    password: string;
    role: 'student' | 'teacher';
}

interface ResetPayloadByOldPassword {
    useremail: string;
    oldPassword: string;
    newPassword: string;
}

interface ResetPayloadByEmail {
    useremail: string;
    verifyCode: string;
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
        async login({ useremail, password, role }: LoginPayload) {
            // 与后端约定只要 HTTP 2xx 就算请求成功
            const response  = await axios.post('/api/login', { useremail, password, role });
            const { status, message, data } = response.data;

            // ❶ 按后端的 status 判断
            if (status !== 'success') {
                throw new Error(message || '登录失败');
            }

            // ❷ 正确写入 state
            this.token     = data.token;
            this.username  = data.username;
            this.role      = data.role;
            this.useremail = useremail;           // state 里加一个 useremail 字段

            // ❸ 本地持久化
            localStorage.setItem('token',     this.token!);
            localStorage.setItem('username',  this.username!);
            localStorage.setItem('role',      this.role!);
            localStorage.setItem('useremail', this.useremail!);
        },

        /** 重置密码 */
        async register(payload: RegisterPayload) {
            await axios.post('/api/register', payload);
            // 注册成功后可直接调用 login() 或跳转到登录页
        },

        /* ===== 旧密码修改 ===== */
        async resetPasswordByOld(payload: ResetPayloadByOldPassword) {
            await axios.post('/api/reset-password/old', payload);
        },

        /* ===== 邮箱验证码修改 ===== */
        async resetPasswordByEmail(payload: ResetPayloadByEmail) {
            await axios.post('/api/reset-password/email', payload);
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
