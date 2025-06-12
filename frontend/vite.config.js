import {fileURLToPath, URL} from 'node:url'
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        }
    },
    server: {
        host: '0.0.0.0',
        proxy: {
            // --- 这是你已有的API代理 ---
            '/cou/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            },
            '/cou/student': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            },
            '/edu/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            },
            '/notifications/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },

            // --- 以下是为聊天室新增的代理规则 ---

            // 1. 为聊天室的 RESTful API 添加代理
            // 你的 chatroom.js 中的请求会发往 /chat/api/...
            '/chat/api': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
                // 重写路径，将 /chat/api 替换为空字符串，因为后端URL配置是从 /chat/api/ 开始的
                rewrite: (path) => path.replace(/^\/chat\/api/, '/chat/api')
            },

            // --- 新增论坛 API 代理规则 ---
            '/forum/api': {
                target: 'http://127.0.0.1:8000', // 你的 Django 后端地址
                changeOrigin: true,
            },

            // --- WebSocket 代理 ---
            '/ws': {
                target: 'ws://127.0.0.1:8000',
                ws: true,
                changeOrigin: true
            }
        }
    }
})