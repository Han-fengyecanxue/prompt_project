/**
 * 格式化工具集
 * 统一"缺失值 -> —"的展示口径, 避免各页面出现 null/undefined/NaN 直出
 */

const DASH = '—'

export const isNil = (v) => v === null || v === undefined || v === ''

/** 通用数字: 千分位 + 最多 d 位小数 */
export function fmtNum(v, d = 2) {
  if (isNil(v)) return DASH
  const n = Number(v)
  if (!Number.isFinite(n)) return DASH
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: d })
}

/** 带符号数字(用于同比/增速) */
export function fmtSigned(v, d = 2) {
  if (isNil(v)) return DASH
  const n = Number(v)
  if (!Number.isFinite(n)) return DASH
  return (n > 0 ? '+' : '') + fmtNum(n, d)
}

/** 金额(元) -> 亿元 */
export function fmtYi(v) {
  if (isNil(v)) return DASH
  const n = Number(v)
  if (!Number.isFinite(n)) return DASH
  return `${(n / 1e8).toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 亿元`
}

/** 金额(元) -> 按量级自动选择 亿元 / 万元 / 元 */
export function fmtMoney(v) {
  if (isNil(v)) return DASH
  const n = Number(v)
  if (!Number.isFinite(n)) return DASH
  const abs = Math.abs(n)
  if (abs >= 1e8) return `${(n / 1e8).toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 亿元`
  if (abs >= 1e4) return `${(n / 1e4).toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 万元`
  return `${n.toLocaleString('zh-CN', { maximumFractionDigits: 2 })} 元`
}

/** 百分比数值(已是 0-100 的数值) */
export function fmtPct(v, d = 2) {
  if (isNil(v)) return DASH
  const n = Number(v)
  if (!Number.isFinite(n)) return DASH
  return `${fmtNum(n, d)}%`
}

export function fmtDate(v) {
  if (isNil(v)) return DASH
  const s = String(v)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (m) return `${m[1]}-${m[2]}-${m[3]}`
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  const p = (x) => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function fmtDateTime(v) {
  if (isNil(v)) return DASH
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return String(v)
  const p = (x) => String(x).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

/** 指标方向文案 */
export function directionText(d) {
  return d === 'lower_better' ? '越低越好' : '越高越好'
}

export function directionArrow(d) {
  return d === 'lower_better' ? '↓' : '↑'
}

/** 评分 -> 等级(与后端"优秀/良好/一般/偏弱"口径一致) */
export function scoreLevel(score) {
  if (isNil(score)) return { text: '无数据', cls: 'mute', tone: 'mute' }
  const s = Number(score)
  if (!Number.isFinite(s)) return { text: '无数据', cls: 'mute', tone: 'mute' }
  if (s >= 75) return { text: '优', cls: 'ok', tone: 'ok' }
  if (s >= 55) return { text: '良', cls: '', tone: 'info' }
  if (s >= 35) return { text: '中', cls: 'warn', tone: 'warn' }
  return { text: '弱', cls: 'bad', tone: 'bad' }
}

/** 综合评级(用于总评分展示) */
export function ratingOf(avgScore) {
  if (isNil(avgScore)) return { text: '暂无评级', cls: 'mute' }
  const s = Number(avgScore)
  if (s >= 70) return { text: '优秀', cls: 'ok' }
  if (s >= 55) return { text: '良好', cls: '' }
  if (s >= 40) return { text: '一般', cls: 'warn' }
  return { text: '偏弱', cls: 'bad' }
}

/** 评分 -> 颜色(与图表配色保持一致) */
export function scoreColor(score) {
  if (isNil(score)) return '#93a3b8'
  const s = Number(score)
  if (s >= 75) return '#10a05a'
  if (s >= 55) return '#2f6fd0'
  if (s >= 35) return '#e2a134'
  return '#d93a44'
}

export const opText = (op) => ({
  gte: '≥', gt: '>', lte: '≤', lt: '<', between: '介于', pct_gt: '高于行业百分位', pct_lt: '低于行业百分位'
}[op] || op)

/** 把对象数组导出为 CSV(带 BOM, Excel 中文不乱码) */
export function downloadCsv(filename, headers, rows) {
  const esc = (v) => {
    const s = v === null || v === undefined ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const lines = [headers.map(esc).join(',')]
  rows.forEach(r => lines.push(r.map(esc).join(',')))
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/** 复制文本到剪贴板(带降级方案) */
export async function copyText(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch { /* 降级 */ }
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  const ok = document.execCommand('copy')
  document.body.removeChild(ta)
  return ok
}
