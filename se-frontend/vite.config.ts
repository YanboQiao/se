import {defineConfig, loadEnv} from 'vite';
import vue from '@vitejs/plugin-vue';
import {fileURLToPath, URL} from 'url';

export default defineConfig(({mode}) => {
    /* 读取 .env、.env.development、.env.production ... */
    const env = loadEnv(mode, process.cwd(), '');

    return {
        plugins: [vue()],

        /* @ → src 别名 */
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url)),
            },
        },

        /* 本地开发服务器配置 */
        server: {
            port: 5173,                 // 前端端口，可自行调整
            proxy: {
                '/api': {
<<<<<<< HEAD
                    target: env.VITE_API_TARGET || 'http://localhost:5000', // ← 后端地址
=======
                    target: env.VITE_API_TARGET || 'http://localhost:1010', // ← 后端地址
>>>>>>> main
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ''),          // 去掉 /api
                },
            },
        },
    };
});