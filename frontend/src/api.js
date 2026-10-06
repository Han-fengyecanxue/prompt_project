/**
 * 后端接口封装
 * - 统一经 Vite 代理 /api -> http://localhost:8091
 * - 统一解包 CommonResponse{code,message,data}: code !== '0' 视为业务失败
 * - 统一超时控制与错误文案, 并附加 err.kind 供 UI 区分"网络 / 超时 / 业务"错误
 */
const BASE = '/api'
const DEFAULT_TIMEOUT = 20000

export class ApiError extends Error {
  constructor(message, { kind = 'business', status = 0, path = '' } = {}) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind          // network | timeout | business | parse
    this.status = status
    this.path = path
  }
}

async function request(path, { timeout = DEFAULT_TIMEOUT, ...options } = {}) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeout)
  let res
  try {
    res = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      signal: ctrl.signal,
      ...options
    })
  } catch (e) {
    clearTimeout(timer)
    if (e && e.name === 'AbortError') {
      throw new ApiError(`请求超时(${timeout / 1000}s), 请检查后端服务是否已启动`, { kind: 'timeout', path })
    }
    throw new ApiError('无法连接后端服务, 请确认已启动 Spring Boot(端口 8091)', { kind: 'network', path })
  }
  clearTimeout(timer)

  let body = null
  try { body = await res.json() } catch { /* 非 JSON 响应 */ }

  if (!res.ok) {
    throw new ApiError((body && body.message) || `请求失败(HTTP ${res.status})`, { kind: 'business', status: res.status, path })
  }
  if (!body) {
    throw new ApiError('响应格式异常: 未返回 JSON 数据', { kind: 'parse', status: res.status, path })
  }
  if (body.code !== '0') {
    throw new ApiError(body.message || '业务处理失败', { kind: 'business', status: res.status, path })
  }
  return body.data
}

const qs = (params = {}) => {
  const q = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, v)
  })
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const api = {
  /** 健康检查: {app,status,database,aiProvider,time} */
  health: () => request('/health', { timeout: 6000 }),

  /** 行业列表: [{industryId,industryCode,industryName,companyCount}] */
  industries: () => request('/finance/industries'),

  /** 指标元数据: [{code,name,dimension,unit,betterDirection}] */
  indicators: () => request('/finance/indicators'),

  /** 公司分页查询: {total,page,size,list} */
  companies: (params = {}) => request(`/finance/companies${qs(params)}`),

  /** 公司详情 */
  company: (id) => request(`/finance/companies/${id}`),

  /** 财务画像: 原始报表科目 + 12 项指标 + 估值快照 */
  profile: (companyId, fiscalYear, reportPeriod = '年报') =>
    request(`/finance/profile${qs({ companyId, fiscalYear, reportPeriod })}`),

  /** 行业对标: 公司 vs 行业基准(均值/中位数/P25/P75/百分位/评分/排名) */
  benchmark: (companyId, fiscalYear, reportPeriod = '年报') =>
    request(`/finance/benchmark${qs({ companyId, fiscalYear, reportPeriod })}`),

  /** 多年度指标趋势: [{indicatorCode,indicatorName,unit,points:[{year,value}]}] */
  trend: (companyId, indicators = [], startYear, endYear) =>
    request(`/finance/trend${qs({
      companyId,
      indicators: indicators.length ? indicators.join(',') : undefined,
      startYear,
      endYear
    })}`),

  /** 行业指标排名(已按名次排序) */
  ranking: (params = {}) => request(`/finance/ranking${qs(params)}`),

  /** 多条件交叉筛选(AND) */
  screening: (payload) => request('/finance/screening', { method: 'POST', body: JSON.stringify(payload) }),

  /** 三层 Prompt 模板(角色设定 / 数据注入 / 输出约束) */
  templates: () => request('/ai/templates'),

  /** 生成财报解读简报 */
  aiReport: (payload) => request('/ai/report', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 }),

  /** 上下文感知追问 */
  aiChat: (payload) => request('/ai/chat', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 }),

  /** 历史报告 / 对话记录(分页) */
  aiReports: (params = {}) => request(`/ai/reports${qs(params)}`),

  /** 重算指标与行业基准(运维用) */
  recalc: (payload = {}) => request('/finance/recalc', { method: 'POST', body: JSON.stringify(payload), timeout: 180000 })
}

/** 系统支持的数据年度(与后端 seed 数据一致) */
export const YEARS = [2021, 2022, 2023, 2024, 2025]
export const LATEST_YEAR = YEARS[YEARS.length - 1]

/** 指标维度展示顺序 */
export const DIMENSIONS = ['盈利能力', '成长性', '财务风险', '盈利质量', '每股指标', '估值']

/** 筛选运算符 */
export const OPERATORS = [
  { v: 'gte', t: '≥', full: '大于或等于' },
  { v: 'gt', t: '>', full: '大于' },
  { v: 'lte', t: '≤', full: '小于或等于' },
  { v: 'lt', t: '<', full: '小于' },
  { v: 'between', t: '介于', full: '介于区间' },
  { v: 'pct_gt', t: '高于行业百分位', full: '高于行业百分位' },
  { v: 'pct_lt', t: '低于行业百分位', full: '低于行业百分位' }
]
