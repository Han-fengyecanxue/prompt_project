/**
 * 全局状态(轻量 store, 仅用 Vue 响应式 API, 不引入 Pinia)
 * 集中管理: 字典数据 / 后端健康状态 / 当前选中公司 / 全局财年 / 通知 / UI 偏好
 * 好处: 各页面不再各自重复拉取 industries 与 indicators, 切换页签无重复请求
 */
import { reactive, computed, readonly } from 'vue'
import { api, YEARS, LATEST_YEAR, DIMENSIONS } from './api'

const LS_KEY = 'fin-ai-ui-v1'

function loadPrefs() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}
function savePrefs() {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      company: state.selectedCompany,
      year: state.year,
      density: state.density,
      sidebarCollapsed: state.sidebarCollapsed
    }))
  } catch { /* 隐私模式下忽略 */ }
}

const prefs = loadPrefs()

const state = reactive({
  /* 字典 */
  industries: [],
  indicators: [],
  industryMap: new Map(),
  indicatorMap: new Map(),
  metaReady: false,
  metaLoading: false,
  metaError: '',

  /* 运行状态 */
  health: null,          // {app,status,database,aiProvider,time}
  healthState: 'unknown', // unknown | ok | degraded | down
  healthChecking: false,

  /* 业务上下文 */
  selectedCompany: prefs.company || null,
  year: prefs.year || LATEST_YEAR,

  /* UI 偏好 */
  density: prefs.density || 'comfortable',
  sidebarCollapsed: prefs.sidebarCollapsed || false,

  /* 通知 */
  toasts: []
})

/* ------------------------------------------------------------------ 派生数据 */
export const dimensions = DIMENSIONS
export const years = YEARS

export const indicatorsByDim = computed(() =>
  DIMENSIONS.map(dim => ({ dim, list: state.indicators.filter(i => i.dimension === dim) }))
    .filter(g => g.list.length)
)

export const companyCount = computed(() =>
  state.industries.reduce((s, i) => s + (i.companyCount || 0), 0)
)

export const metaOf = (code) => state.indicatorMap.get(code) || null

/* ------------------------------------------------------------------ 通知 */
let toastSeq = 0
export function toast(message, type = 'info', duration = 3200) {
  const id = ++toastSeq
  state.toasts.push({ id, message, type })
  if (duration > 0) setTimeout(() => dismissToast(id), duration)
  return id
}
export function dismissToast(id) {
  const i = state.toasts.findIndex(t => t.id === id)
  if (i >= 0) state.toasts.splice(i, 1)
}

/* ------------------------------------------------------------------ 动作 */
export async function bootstrap() {
  state.metaLoading = true
  state.metaError = ''
  try {
    const [industries, indicators] = await Promise.all([api.industries(), api.indicators()])
    state.industries = industries
    state.indicators = indicators
    state.industryMap = new Map(industries.map(i => [i.industryId, i]))
    state.indicatorMap = new Map(indicators.map(i => [i.code, i]))
    state.metaReady = true
  } catch (e) {
    state.metaError = e.message
  } finally {
    state.metaLoading = false
  }
}

export async function checkHealth() {
  state.healthChecking = true
  try {
    const h = await api.health()
    state.health = h
    state.healthState = h.database === 'UP' ? 'ok' : 'degraded'
  } catch {
    state.health = null
    state.healthState = 'down'
  } finally {
    state.healthChecking = false
  }
}

export function selectCompany(company) {
  if (!company || !company.companyId) return
  const prev = state.selectedCompany
  // 行业排行/筛选返回的公司对象字段较少, 与已有对象合并, 避免丢失行业名等信息
  state.selectedCompany = prev && prev.companyId === company.companyId
    ? { ...prev, ...company }
    : { ...company }
  if (state.selectedCompany.industryId && !state.selectedCompany.industryName) {
    const ind = state.industryMap.get(state.selectedCompany.industryId)
    if (ind) state.selectedCompany.industryName = ind.industryName
  }
  savePrefs()
}

export function setYear(y) {
  state.year = Number(y) || LATEST_YEAR
  savePrefs()
}

export function toggleDensity() {
  state.density = state.density === 'compact' ? 'comfortable' : 'compact'
  applyDensity()
  savePrefs()
}

export function applyDensity() {
  document.documentElement.setAttribute('data-density', state.density)
}

export function toggleSidebar() {
  state.sidebarCollapsed = !state.sidebarCollapsed
  savePrefs()
}

export function industryName(id) {
  const i = state.industryMap.get(Number(id))
  return i ? i.industryName : ''
}

/** 只读视图(推荐在展示型组件中使用); store 为可直接解构读取的别名 */
export const ui = readonly(state)
export const store = state
export { state }
