import { defineStore } from 'pinia';
import axios from 'axios';

interface UserState {
  token: string | null;
  username: string | null;
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: localStorage.getItem('token'),
    username: localStorage.getItem('username'),
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },

  actions: {
    async login(username: string, password: string) {
      // ❗ TODO: 替换为真实后端接口
      const res = await axios.post('/api/login', { username, password });
      this.token    = res.data.token;
      this.username = username;
      localStorage.setItem('token',    this.token!);
      localStorage.setItem('username', this.username!);
    },

    logout() {
      this.token = null;
      this.username = null;
      localStorage.removeItem('token');
      localStorage.removeItem('username');
    },
  },
});
