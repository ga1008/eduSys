import {fileURLToPath, URL} from 'node:url'
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            // 在这里把 '@' 指向 './src'
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        }
    },
    server: {
        host: '0.0.0.0', // 关键修改：绑定到所有网络接口
        proxy: {
            '/cou/api': {
                target: 'http://127.0.0.1:8000',  // Django后端地址
                changeOrigin: true
            },
            '/cou/student': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            },
            '/edu/api': {  // 如果有其他API也需要代理
                target: 'http://127.0.0.1:8000',
                changeOrigin: true
            },
            // --- 新增的代理规则 ---
            '/notifications/api': {
                target: 'http://127.0.0.1:8000', // 同样指向 Django 后端
                changeOrigin: true,
                // 可选：重写路径，如果 Django 的 URL 配置不包含 /notifications/api 前缀
                // rewrite: (path) => path.replace(/^\/notifications\/api/, '/api/notifications')
            }
        }
    }
})