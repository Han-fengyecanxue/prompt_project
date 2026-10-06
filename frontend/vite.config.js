import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

/**
 * 前端构建配置
 * - 开发服务器 5173, /api 代理到后端 8091(避免跨域, 前端代码里统一用相对路径 /api)
 * - base 使用相对路径: 打包产物 dist 既可直接双击 index.html 预览, 也可放到任意子目录部署
 * - 手动分包: 把 echarts / vue 拆成独立 chunk, 便于浏览器缓存, 也避免单个文件过大
 */
export default defineConfig({
  plugins: [vue()],
  base: './',
  server: {
    port: 5173,
    host: true,
    // 忽略编辑器写入过程中的临时目录, 避免触发 FSWatcher EBUSY 导致 dev server 退出
    watch: {
      ignored: ['**/*.tmpdir/**', '**/.*.tmpdir/**', '**/.git/**']
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8091',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8091',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('echarts') || id.includes('zrender')) return 'vendor-echarts'
          if (id.includes('/vue/') || id.includes('@vue')) return 'vendor-vue'
          return 'vendor'
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    }
  }
})
