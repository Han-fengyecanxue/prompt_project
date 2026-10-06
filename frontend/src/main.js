import { createApp } from 'vue'
import App from './App.vue'
import './styles/tokens.css'
import './styles/base.css'

// 启动前应用本地 UI 偏好, 避免首屏闪烁
try {
  const raw = localStorage.getItem('fin-ai-ui-v1')
  if (raw) {
    const p = JSON.parse(raw)
    if (p.density) document.documentElement.setAttribute('data-density', p.density)
  }
} catch { /* 忽略隐私模式下的异常 */ }

const app = createApp(App)

// 兜底: 未捕获的渲染错误不至于白屏, 同时把组件名打出来便于定位
app.config.errorHandler = (err, instance, info) => {
  const name = (instance && (instance.$options?.name || instance.$options?.__name)) || '未知组件'
  console.error(`[vue error] 组件=${name} 阶段=${info}`, err)
}

app.mount('#app')

// 首屏占位移除
const boot = document.getElementById('boot')
if (boot) boot.remove()
