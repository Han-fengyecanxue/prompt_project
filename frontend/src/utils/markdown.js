/**
 * 轻量 Markdown 渲染
 * 安全策略: 先整体 HTML 转义, 再套用受控的排版标签, 全程不注入原始 HTML —— 从根上杜绝 XSS。
 * 附加能力: 数值溯源高亮 —— 报告中出现的数字, 若能在系统计算的指标/对标数据里找到出处则标绿,
 *          找不到出处的标黄, 用于直观呈现"防幻觉"这一项目核心创新点。
 */

export function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** 行内语法: 粗体 / 行内代码 / 斜体 */
function inlineMd(s, opts) {
  let out = s
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/`([^`]+?)`/g, '<code>$1</code>')
    .replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<i>$2</i>')
  if (opts && opts.highlight) out = highlightNumbers(out, opts.known)
  return out
}

/**
 * 数字 token 匹配
 * 前置断言 `(?<![A-Za-z_])` 用于排除 "P75""P25""C39""ROE" 这类标识符里的数字,
 * 否则统计分位数 P75 会被误判成"报告中出现了 75 这个数字"。
 */
const NUM_RE = /(?<![A-Za-z_])(-?\d+(?:\.\d+)?)/g

/** 该 token 是否值得纳入溯源统计(排除年份、章节序号、股票代码等非指标数字) */
function isMeaningfulNumber(tok) {
  const n = Math.abs(Number(tok))
  if (!Number.isFinite(n)) return false
  if (Number.isInteger(n) && n <= 12) return false                 // 章节号 / 条件序号
  if (Number.isInteger(n) && n >= 1900 && n <= 2100) return false   // 年份
  if (Number.isInteger(n) && n >= 100000 && n <= 999999) return false // 6 位股票代码
  return true
}

/** 数值是否能在已知数据中找到出处(允许 1 位小数/取整的表述差异) */
function matched(v, known) {
  return known.some(k => Math.abs(k - v) <= Math.max(0.011, Math.abs(k) * 0.0015))
}

/**
 * 在已转义的行内 HTML 上标注数字。
 * 注意: 只处理标签之外的文本片段, 避免把 class="h4" 里的数字染色。
 */
function highlightNumbers(html, known) {
  if (!known || !known.length) return html
  return html.split(/(<[^>]+>)/g).map(seg => {
    if (seg.startsWith('<')) return seg
    return seg.replace(NUM_RE, (tok) => {
      if (!isMeaningfulNumber(tok)) return tok
      return matched(Number(tok), known)
        ? `<span class="num-hit" title="该数值可在系统计算数据中溯源">${tok}</span>`
        : `<span class="num-miss" title="该数值未在系统计算数据中匹配到出处, 建议人工核对">${tok}</span>`
    })
  }).join('')
}

/**
 * Markdown -> HTML
 * @param {string} text
 * @param {{known?: number[], highlight?: boolean}} opts
 */
export function renderMarkdown(text, opts = {}) {
  if (!text) return ''
  const src = escapeHtml(text).replace(/\r\n?/g, '\n')
  const lines = src.split('\n')
  const out = []
  let listType = null   // 'ul' | 'ol'
  let inQuote = false
  let tableBuf = []

  const closeList = () => { if (listType) { out.push(`</${listType}>`); listType = null } }
  const closeQuote = () => { if (inQuote) { out.push('</blockquote>'); inQuote = false } }
  const flushTable = () => {
    if (!tableBuf.length) return
    const rows = tableBuf.map(r => r.split('|').map(c => c.trim()).filter((_, i, a) => !(i === 0 && !a[0]) && !(i === a.length - 1 && !a[a.length - 1])))
    const head = rows[0]
    const body = rows.slice(1).filter(r => !r.every(c => /^:?-{2,}:?$/.test(c)))
    out.push('<div class="md-table-wrap"><table class="md-table"><thead><tr>' +
      head.map(h => `<th>${inlineMd(h, opts)}</th>`).join('') + '</tr></thead><tbody>' +
      body.map(r => '<tr>' + r.map(c => `<td>${inlineMd(c, opts)}</td>`).join('') + '</tr>').join('') +
      '</tbody></table></div>')
    tableBuf = []
  }

  for (const raw of lines) {
    const line = raw.replace(/\s+$/, '')

    // 表格行
    if (/^\s*\|.*\|\s*$/.test(line)) { closeList(); closeQuote(); tableBuf.push(line.trim()); continue }
    flushTable()

    if (!line.trim()) { closeList(); closeQuote(); continue }

    const h = line.match(/^(#{1,6})\s+(.*)$/)
    if (h) {
      closeList(); closeQuote()
      const lv = Math.min(h[1].length, 4)
      out.push(`<h${lv} class="md-h md-h${lv}">${inlineMd(h[2], opts)}</h${lv}>`)
      continue
    }

    if (/^\s*(?:[-*•]|—)\s+/.test(line)) {
      closeQuote()
      if (listType !== 'ul') { closeList(); out.push('<ul class="md-ul">'); listType = 'ul' }
      out.push(`<li>${inlineMd(line.replace(/^\s*(?:[-*•]|—)\s+/, ''), opts)}</li>`)
      continue
    }

    if (/^\s*\d+[.、)]\s+/.test(line)) {
      closeQuote()
      if (listType !== 'ol') { closeList(); out.push('<ol class="md-ol">'); listType = 'ol' }
      out.push(`<li>${inlineMd(line.replace(/^\s*\d+[.、)]\s+/, ''), opts)}</li>`)
      continue
    }

    if (/^\s*>\s?/.test(line)) {
      closeList()
      if (!inQuote) { out.push('<blockquote class="md-quote">'); inQuote = true }
      out.push(`<p>${inlineMd(line.replace(/^\s*>\s?/, ''), opts)}</p>`)
      continue
    }

    if (/^\s*(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
      closeList(); closeQuote(); out.push('<hr class="md-hr">'); continue
    }

    closeList(); closeQuote()
    out.push(`<p class="md-p">${inlineMd(line, opts)}</p>`)
  }
  closeList(); closeQuote(); flushTable()
  return out.join('\n')
}

/**
 * 数值溯源校验: 统计文本中的数字有多少能在已知数据中找到出处。
 * @returns {{total:number, matched:number, missing:number, ratio:number, missingList:string[]}}
 */
export function verifyNumbers(text, known) {
  const set = (known || []).filter(v => Number.isFinite(v))
  const tokens = String(text || '').match(NUM_RE) || []
  const meaningful = tokens.filter(isMeaningfulNumber)
  let matchedCount = 0
  const missingList = []
  for (const t of meaningful) {
    if (matched(Number(t), set)) matchedCount++
    else if (missingList.length < 8 && !missingList.includes(t)) missingList.push(t)
  }
  const total = meaningful.length
  return {
    total,
    matched: matchedCount,
    missing: total - matchedCount,
    ratio: total ? Math.round((matchedCount / total) * 1000) / 10 : 100,
    missingList
  }
}

/** 从画像/对标数据里收集所有可溯源的数值 */
export function collectKnownNumbers(profile, benchmark) {
  const out = []
  const push = (v) => { const n = Number(v); if (Number.isFinite(n)) out.push(n) }
  ;(profile && profile.indicators || []).forEach(i => push(i.value))
  ;(profile && profile.items || []).forEach(i => { push(i.amount); push(Number(i.amount) / 1e8) })
  if (profile && profile.valuation) {
    push(profile.valuation.closePrice)
    push(Number(profile.valuation.marketCap) / 1e8)
  }
  const items = (benchmark && benchmark.items) || []
  items.forEach(i => {
    push(i.companyValue); push(i.avgValue); push(i.medianValue)
    push(i.p25); push(i.p75); push(i.percentile); push(i.score); push(i.rank); push(i.total)
  })
  // 综合评分(各指标方向调整评分的均值)也是系统算出来的, 报告中会引用, 需纳入可溯源集合
  const scores = items.map(i => Number(i.score)).filter(Number.isFinite)
  if (scores.length) {
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length
    push(Math.round(avg * 10) / 10)
    push(Math.round(avg))
  }
  // 对标基准线(中位水平恒为 50 分)与百分制上下限
  push(50); push(100); push(0)
  // 兼容"约 28.6%"这类一位小数/取整表述
  const extra = []
  out.forEach(v => { extra.push(Math.round(v * 10) / 10); extra.push(Math.round(v)) })
  return [...out, ...extra]
}
