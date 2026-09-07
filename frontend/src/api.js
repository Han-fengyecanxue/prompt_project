// 后端接口封装(经 Vite 代理 /api -> localhost:8091)
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  const body = await res.json().catch(() => null)
  if (!res.ok || !body || body.code !== '0') {
    throw new Error((body && body.message) || `请求失败(HTTP ${res.status})`)
  }
  return body.data
}

export const api = {
  health: () => request('/health'),

  industries: () => request('/finance/industries'),

  // 全部指标元数据: [{code,name,dimension,unit,betterDirection}]
  indicators: () => request('/finance/indicators'),

  companies: (params = {}) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') q.set(k, v) })
    return request(`/finance/companies?${q.toString()}`)
  },

  profile: (companyId, fiscalYear, reportPeriod = '年报') =>
    request(`/finance/profile?companyId=${companyId}&fiscalYear=${fiscalYear}&reportPeriod=${encodeURIComponent(reportPeriod)}`),

  benchmark: (companyId, fiscalYear, reportPeriod = '年报') =>
    request(`/finance/benchmark?companyId=${companyId}&fiscalYear=${fiscalYear}&reportPeriod=${encodeURIComponent(reportPeriod)}`),

  trend: (companyId, indicators = [], startYear, endYear) => {
    const q = new URLSearchParams({ companyId })
    if (indicators.length) q.set('indicators', indicators.join(','))
    if (startYear) q.set('startYear', startYear)
    if (endYear) q.set('endYear', endYear)
    return request(`/finance/trend?${q.toString()}`)
  },

  // 行业指标排名: 返回按名次排好的数组
  ranking: (params = {}) => {
    const q = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') q.set(k, v) })
    return request(`/finance/ranking?${q.toString()}`)
  },

  // 多条件交叉筛选(AND): {industryId?, fiscalYear, reportPeriod, conditions:[...], page, size}
  screening: (payload) => request('/finance/screening', { method: 'POST', body: JSON.stringify(payload) }),

  aiReport: (payload) => request('/ai/report', { method: 'POST', body: JSON.stringify(payload) }),
  aiChat: (payload) => request('/ai/chat', { method: 'POST', body: JSON.stringify(payload) })
}

export const YEARS = [2021, 2022, 2023, 2024, 2025]

// 金额(元) -> 亿元 显示
export function fmtYi(v) {
  if (v === null || v === undefined) return '—'
  return (v / 1e8).toLocaleString('zh-CN', { maximumFractionDigits: 2 }) + ' 亿元'
}

// 数字显示(去掉多余的 0)
export function fmtNum(v) {
  if (v === null || v === undefined) return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

// 指标方向文案
export function directionText(d) {
  return d === 'lower_better' ? '↓ 越低越好' : '↑ 越高越好'
}
