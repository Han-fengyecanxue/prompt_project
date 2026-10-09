<script setup>
/**
 * 应用外壳: 左侧导航 + 顶栏 + 内容区
 * - 图表页(概览/画像)
 * - 交互页(查询/排行/筛选/AI)
 */
import { ref, computed, onMounted, onBeforeUnmount, shallowRef } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'
import ToastHost from './components/ToastHost.vue'
import DashboardView from './views/DashboardView.vue'
import CompanyListView from './views/CompanyListView.vue'
import ProfileView from './views/ProfileView.vue'
import AiView from './views/AiView.vue'
import RankingView from './views/RankingView.vue'
import ScreeningView from './views/ScreeningView.vue'
import { api } from './api'
import { bootstrap, checkHealth, selectCompany, applyDensity, store, toast } from './store'

const VIEWS = {
  dashboard: DashboardView,
  list: CompanyListView,
  profile: ProfileView,
  ai: AiView,
  ranking: RankingView,
  screening: ScreeningView
}

const active = ref('dashboard')
const currentView = shallowRef(DashboardView)
const KEEP_ALIVE = ['AiView', 'CompanyListView', 'ScreeningView']

/** 解析 #/view/companyId 形式的路由 */
function parseHash() {
  const raw = String(location.hash || '').replace(/^#\/?/, '')
  const [key, id] = raw.split('/')
  return { key: VIEWS[key] ? key : 'dashboard', companyId: id ? Number(id) : null }
}

function navigate(key, replace = false) {
  if (!VIEWS[key]) return
  const target = `#/${key}`
  if (location.hash !== target) {
    if (replace) history.replaceState(null, '', target)
    else location.hash = target
  }
  applyRoute()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** 根据当前 hash 切换视图, 并按需载入深链中的公司 */
async function applyRoute() {
  const { key, companyId } = parseHash()
  active.value = key
  currentView.value = VIEWS[key]
  if (companyId && (!store.selectedCompany || store.selectedCompany.companyId !== companyId)) {
    try {
      const c = await api.company(companyId)
      if (c) selectCompany(c)
    } catch { /* 深链失效时静默降级 */ }
  }
}

/** 子视图请求"查看某公司画像": 写入 hash, 使地址栏可分享 */
function onSelect(company) {
  selectCompany(company)
  const id = company && company.companyId ? `/${company.companyId}` : ''
  const target = `#/profile${id}`
  if (location.hash === target) applyRoute()
  else location.hash = target
}

function onHashChange() { applyRoute() }

let healthTimer = 0
onMounted(async () => {
  applyDensity()
  window.addEventListener('hashchange', onHashChange)
  await applyRoute()
  await checkHealth()
  await bootstrap()
  if (store.metaError) toast(`字典数据加载失败: ${store.metaError}`, 'error', 6000)
  healthTimer = setInterval(checkHealth, 60000)
})
onBeforeUnmount(() => {
  clearInterval(healthTimer)
  window.removeEventListener('hashchange', onHashChange)
})

const metaFailed = computed(() => !store.metaLoading && !store.metaReady)
</script>

<template>
  <div class="app">
    <AppSidebar :active="active" @navigate="navigate" />

    <div class="main-col">
      <AppTopbar :active="active" />

      <main class="content">
        <div class="content-inner">
          <div v-if="metaFailed" class="alert mt-2 no-print" role="alert">
            <span>⛔</span>
            <div>
              <b>基础数据加载失败。</b>{{ store.metaError }}
              <div class="muted mt-1">请确认后端已启动: 双击项目根目录「启动后端.bat」,或执行
                <code>java -jar backend/target/prompt_project-0.0.1-SNAPSHOT.jar</code>(端口 8091)。</div>
            </div>
            <button class="btn btn-ghost btn-sm" style="margin-left:auto" @click="bootstrap()">重试</button>
          </div>

          <KeepAlive :include="KEEP_ALIVE">
            <component :is="currentView" @select="onSelect" @navigate="navigate" />
          </KeepAlive>
        </div>

        <footer class="app-footer">
          <span>上市公司财报解读与行业对标系统</span>
          <span class="sep">|</span>
          <span>Spring Boot + Vue 底层精确计算 + 上层 Prompt 工程生成解读</span>
          <span class="sep">|</span>
          <span>数据来源: 东方财富 / 新浪公开财报接口 · 仅供学习研究, 不构成投资建议</span>
        </footer>
      </main>
    </div>

    <ToastHost />
  </div>
</template>

<style scoped>
.app { display: flex; min-height: 100vh; background: var(--c-bg); }
.main-col { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.content { flex: 1; padding: var(--sp-5) var(--sp-6) var(--sp-6); min-width: 0; }
.content-inner { max-width: var(--content-max); margin: 0 auto; display: flex; flex-direction: column; gap: var(--sp-5); }

.app-footer {
  max-width: var(--content-max); margin: var(--sp-7) auto 0;
  padding-top: var(--sp-4); border-top: 1px solid var(--c-border);
  display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
  font-size: 12px; color: var(--c-text-3); text-align: center;
}
.sep { color: var(--c-border-2); }
@media (max-width: 720px) { .sep { display: none; } }
@media (max-width: 860px) {
  .app { display: block; }
  .content { padding: var(--sp-4) var(--sp-4) var(--sp-6); }
}
</style>
