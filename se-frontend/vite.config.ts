/* vite.config.ts / vite.config.js */

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'url'

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')

    return {
        plugins: [vue()],
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url)),
            },
        },
        server: {
            /** ↓↓↓ 关键：监听所有接口（IPv4+IPv6） ↓↓↓ */
            host: '::',          // 若只想 IPv4，可写 '0.0.0.0'
            port: 5173,
            proxy: {
                '/api': {
                    target: env.VITE_API_TARGET || 'http://localhost:1010',
                    changeOrigin: true,
                },
            },
        },
    }
})