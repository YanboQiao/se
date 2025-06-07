import axios, { AxiosRequestHeaders } from 'axios';
import {useUserStore} from '@/stores/user';

/**
 * BASE_URL 读取顺序：
 * 1. 先看 .env.[mode] 里是否定义 VITE_API_BASE
 * 2. 若未定义则默认走 '/api'（配合 Vite 代理到 1010 端口）
 */
const BASE_URL = import.meta.env.VITE_API_BASE || '/api';

const http = axios.create({
    baseURL: BASE_URL,
    timeout: 10000,
});

/* 在每次请求头自动带上 token 和用户邮箱 */
http.interceptors.request.use((config) => {
    const store = useUserStore();
    if (store.token) {
        config.headers = config.headers || {} as AxiosRequestHeaders;
        config.headers.Authorization = `Bearer ${store.token}`;
    }
    if (store.useremail) {
        config.headers = config.headers || {} as AxiosRequestHeaders;
        config.headers['X-User-Email'] = store.useremail;
    }
    return config;
});

export default http;
