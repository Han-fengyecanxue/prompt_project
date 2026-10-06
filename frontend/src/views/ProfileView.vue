<script setup>
/**
 * 财务画像 · 行业对标
 * 结构: 公司总览 -> 关键指标卡 -> 六维能力雷达 -> 指标趋势 -> 行业对标(图 + 明细表) -> 指标速览 -> 报表科目
 * 数据: /api/finance/profile + /api/finance/benchmark + /api/finance/trend
 */
import { ref, computed, watch, onMounted } from 'vue'
import { api, DIMENSIONS } from '../api'
import { store, toast } from '../store'
import EChart from '../components/EChart.vue'
import StatCard from '../components/StatCard.vue'
import EmptyState from '../components/EmptyState.vue'
import IndicatorTip from '../components/IndicatorTip.vue'
import {
  categoryAxis, valueAxis, tooltip, legend, PALETTE, emptyOption
} from '../utils/charts'
import {
  fmtNum, fmtYi, fmtMoney, scoreLevel, scoreColor,
  ratingOf, directionText, downloadCsv
} from '../utils/format'

defineOptions({ name: 'ProfileView' })
const emit = defineEmits(['select', 'navigate'])

const company = computed(() => store.selectedCompany)
const year = computed(() => store.year)

const loading = ref(false)
const err = ref('')
const profile = ref(null)
const benchmark = ref(null)
const trendRaw = ref([])
const trendCodes = ref(['roe', 'gross_margin', 'asset_liability_ratio', 'revenue_growth'])
const sortKey = ref('score')
const sortDir = ref('desc')

const TREND_CHOICES = [
  ['roe', 'ROE'], ['gross_margin', '毛利率'], ['net_margin_parent', '归母净利率'],
  ['revenue_growth', '营收增速'], ['profit_growth', '净利增速'],
  ['asset_liability_ratio', '资产负债率'], ['current_ratio', '流动比率'],
  ['quick_ratio', '速动比率'], ['cashflow_quality', '现金流/净利'],
  ['eps', '每股收益'], ['pe', '市盈率PE'], ['pb', '市净率PB']
]

async function load() {
  if (!company.value || !company.value.companyId) return
  loading.value = true
  err.value = ''
  try {
    const [p, b, t] = await Promise.all([
      api.profile(company.value.companyId, year.value),
      api.benchmark(company.value.companyId, year.value),
      api.trend(company.value.companyId)
    ])
    profile.value = p
    benchmark.value = b
    trendRaw.value = t || []
  } catch (e) {
    err.value = e.message
    profile.value = null
    benchmark.value = null
    trendRaw.value = []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(company, load)
watch(year, () => { load(); toast(`已切换到 ${year.value} 年报`, 'info', 1600) })

/* ------------------------------------------------------------- 派生数据 */
const items = computed(() => (benchmark.value && benchmark.value.items) || [])
const pick = (code) => items.value.find(i => i.indicatorCode === code) || null

const avgScore = computed(() => {
  const s = items.value.map(i => Number(i.score)).filter(Number.isFinite)
  return s.length ? Math.round((s.reduce((a, b) => a + b, 0) / s.length) * 10) / 10 : null
})
const rating = computed(() => ratingOf(avgScore.value))

const best = computed(() => [...items.value].filter(i => Number.isFinite(Number(i.score))).sort((a, b) => b.score - a.score).slice(0, 3))
const worst = computed(() => [...items.value].filter(i => Number.isFinite(Number(i.score))).sort((a, b) => a.score - b.score).slice(0, 3))

/** 六维得分: 维度内各指标的方向调整评分均值 */
const dimScores = computed(() => DIMENSIONS.map(dim => {
  const list = items.value.filter(i => i.dimension === dim && Number.isFinite(Number(i.score)))
  return {
    dim,
    score: list.length ? Math.round(list.reduce((s, i) => s + Number(i.score), 0) / list.length * 10) / 10 : null,
    count: list.length
  }
}).filter(d => d.count))

/** 关键指标卡: [指标编码, 展示名, 单位提示] */
const KPIS = [
  ['roe', '净资产收益率', '盈利核心'],
  ['gross_margin', '毛利率', '产品竞争力'],
  ['asset_liability_ratio', '资产负债率', '财务风险'],
  ['revenue_growth', '营收增长率', '成长性'],
  ['pe', '市盈率 PE', '估值水平']
]

const yearRange = computed(() => {
  const ys = trendRaw.value.flatMap(t => (t.points || []).map(p => p.year))
  return ys.length ? [Math.min(...ys), Math.max(...ys)] : [2021, 2025]
})

/* ------------------------------------------------------------- 图表 option */
const radarOption = computed(() => {
  const dims = dimScores.value
  if (!dims.length) return emptyOption('暂无对标数据')
  return {
    tooltip: tooltip({ trigger: 'item' }),
    legend: legend({ bottom: 0, left: 'center', data: ['本公司得分', '行业中位基准'] }),
    radar: {
      center: ['50%', '47%'],
      radius: '74%',
      splitNumber: 4,
      indicator: dims.map(d => ({ name: d.dim, max: 100 })),
      axisName: { color: '#52637a', fontSize: 12 },
      splitLine: { lineStyle: { color: '#e6edf6' } },
      splitArea: { areaStyle: { color: ['rgba(247,249,252,.6)', 'rgba(255,255,255,.6)'] } },
      axisLine: { lineStyle: { color: '#e6edf6' } }
    },
    series: [{
      type: 'radar',
      symbolSize: 5,
      data: [
        {
          value: dims.map(d => d.score),
          name: '本公司得分',
          areaStyle: { color: 'rgba(47,111,208,.22)' },
          lineStyle: { color: '#2f6fd0', width: 2 },
          itemStyle: { color: '#2f6fd0' }
        },
        {
          value: dims.map(() => 50),
          name: '行业中位基准',
          areaStyle: { color: 'rgba(147,163,184,.10)' },
          lineStyle: { color: '#93a3b8', width: 1.5, type: 'dashed' },
          itemStyle: { color: '#93a3b8' }
        }
      ]
    }]
  }
})

const trendOption = computed(() => {
  const [y0, y1] = yearRange.value
  const years = []
  for (let y = y0; y <= y1; y++) years.push(y)
  const chosen = trendCodes.value
  const units = new Set()
  const series = trendRaw.value
    .filter(t => chosen.includes(t.indicatorCode))
    .map(t => {
      units.add(t.unit)
      return {
        name: t.indicatorName,
        type: 'line',
        smooth: true,
        connectNulls: true,
        symbolSize: 6,
        emphasis: { focus: 'series' },
        data: years.map(y => {
          const pt = (t.points || []).find(p => p.year === y)
          return pt && pt.value !== null && pt.value !== undefined ? Number(pt.value) : null
        })
      }
    })
  return {
    color: PALETTE,
    tooltip: tooltip({
      trigger: 'axis',
      formatter(ps) {
        const head = `<b>${ps[0].axisValue}</b> 年报`
        const rows = ps.map(p => {
          const unit = findUnitByName(p.seriesName)
          return `${p.marker} ${p.seriesName} <b>${p.value === null || p.value === undefined ? '—' : fmtNum(p.value)}</b> ${unit}`
        })
        return [head, ...rows].join('<br/>')
      }
    }),
    legend: legend({ top: 0, type: 'scroll' }),
    grid: { left: 8, right: 22, top: 40, bottom: 6, containLabel: true },
    xAxis: categoryAxis(years.map(y => `${y}年`), { boundaryGap: false, axisLabel: { color: '#8a97a8', fontSize: 11 } }),
    yAxis: valueAxis({ scale: true }),
    series
  }
})

function findUnitByName(name) {
  const t = trendRaw.value.find(x => x.indicatorName === name)
  return t ? t.unit : ''
}

const sortedItems = computed(() => {
  const arr = [...items.value]
  const k = sortKey.value, dir = sortDir.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    const av = a[k], bv = b[k]
    if (av === null || av === undefined) return 1
    if (bv === null || bv === undefined) return -1
    if (typeof av === 'string') return av.localeCompare(bv) * dir
    return (av - bv) * dir
  })
  return arr
})

const benchOption = computed(() => {
  const list = [...items.value].filter(i => i.score !== null && i.score !== undefined)
  if (!list.length) return emptyOption('暂无对标数据')
  const sorted = list.sort((a, b) => Number(a.score) - Number(b.score))
  return {
    tooltip: tooltip({
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(ps) {
        const it = sorted[ps[0].dataIndex]
        const lv = scoreLevel(it.score)
        return [
          `<b>${it.indicatorName}</b> <span style="color:#8a97a8">${it.dimension}</span>`,
          `本公司: <b>${fmtNum(it.companyValue)}</b> ${it.unit}（行业排名 ${it.rank}/${it.total}）`,
          `行业中位数: ${fmtNum(it.medianValue)} ${it.unit} ｜ 行业均值: ${fmtNum(it.avgValue)}`,
          `P25–P75: ${fmtNum(it.p25)} ~ ${fmtNum(it.p75)}`,
          `原始百分位: ${fmtNum(it.percentile)} ｜ 方向调整评分: <b>${fmtNum(it.score)}</b>（${lv.text}）`,
          `<span style="color:#8a97a8">指标方向: ${directionText(it.betterDirection)}</span>`
        ].join('<br/>')
      }
    }),
    legend: legend({ top: 0, data: ['方向调整评分', '原始百分位'] }),
    grid: { left: 8, right: 74, top: 38, bottom: 4, containLabel: true },
    xAxis: valueAxis({ min: 0, max: 100, splitLine: { lineStyle: { color: '#f2f5f9', type: 'dashed' } } }),
    yAxis: categoryAxis(sorted.map(i => i.indicatorName), {
      axisLabel: { fontSize: 11, color: '#52637a', width: 96, overflow: 'truncate' }
    }),
    series: [
      {
        name: '方向调整评分',
        type: 'bar',
        barWidth: 8,
        barGap: '30%',
        data: sorted.map(it => ({
          value: Number(it.score),
          itemStyle: { color: scoreColor(it.score), borderRadius: [0, 4, 4, 0] }
        })),
        label: {
          show: true, position: 'right', fontSize: 10.5, color: '#52637a',
          formatter: p => fmtNum(p.value, 1)
        }
      },
      {
        name: '原始百分位',
        type: 'bar',
        barWidth: 8,
        itemStyle: { color: '#c9d6e5', borderRadius: [0, 4, 4, 0] },
        data: sorted.map(it => (it.percentile === null ? null : Number(it.percentile)))
      }
    ]
  }
})

/** 报表科目: 按报表分组, 组内按金额绝对值排序并给出相对条形 */
const reportGroups = computed(() => {
  const list = (profile.value && profile.value.items) || []
  const map = new Map()
  list.forEach(it => {
    const g = it.reportType || '其他'
    if (!map.has(g)) map.set(g, [])
    map.get(g).push(it)
  })
  return [...map.entries()].map(([type, arr]) => {
    const max = Math.max(...arr.map(x => Math.abs(Number(x.amount) || 0))) || 1
    return {
      type,
      list: [...arr].sort((a, b) => Math.abs(Number(b.amount) || 0) - Math.abs(Number(a.amount) || 0)).map(x => ({
        ...x,
        pct: Math.round((Math.abs(Number(x.amount) || 0) / max) * 100)
      }))
    }
  })
})

/* ------------------------------------------------------------- 交互 */
function toggleTrend(code) {
  const i = trendCodes.value.indexOf(code)
  if (i >= 0) {
    if (trendCodes.value.length === 1) { toast('至少保留一个指标', 'warn', 1800); return }
    trendCodes.value = trendCodes.value.filter(c => c !== code)
  } else {
    if (trendCodes.value.length >= 6) { toast('最多同时对比 6 个指标, 以保证图表可读性', 'warn', 2200); return }
    trendCodes.value = [...trendCodes.value, code]
  }
}

function sortBy(k) {
  if (sortKey.value === k) sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  else { sortKey.value = k; sortDir.value = 'desc' }
}
const arrow = (k) => (sortKey.value === k ? (sortDir.value === 'asc' ? '▲' : '▼') : '')

function exportCsv() {
  if (!items.value.length) return
  const headers = ['指标', '维度', '单位', '本公司值', '行业中位数', '行业均值', 'P25', 'P75', '百分位', '评分', '排名', '行业样本数', '指标方向']
  const rows = items.value.map(i => [
    i.indicatorName, i.dimension, i.unit, i.companyValue, i.medianValue, i.avgValue,
    i.p25, i.p75, i.percentile, i.score, `${i.rank}/${i.total}`, i.total, directionText(i.betterDirection)
  ])
  const name = `${company.value.stockName}_${year.value}年_行业对标明细.csv`
  downloadCsv(name, headers, rows)
  toast(`已导出 ${name}`, 'ok')
}

function exportTrendCsv() {
  if (!trendRaw.value.length) return
  const headers = ['指标', '单位', ...yearRangeList()]
  const rows = trendRaw.value.map(t => [
    t.indicatorName, t.unit,
    ...yearRangeList().map(y => {
      const pt = (t.points || []).find(p => p.year === y)
      return pt ? pt.value : ''
    })
  ])
  const name = `${company.value.stockName}_核心指标趋势.csv`
  downloadCsv(name, headers, rows)
  toast(`已导出 ${name}`, 'ok')
}
function yearRangeList() {
  const [a, b] = yearRange.value
  const out = []
  for (let y = a; y <= b; y++) out.push(y)
  return out
}

const goAi = () => emit('navigate', 'ai')
/** 打印(模板中无法直接访问 window, 故包一层) */
const doPrint = () => window.print()
</script>

<template>
  <div class="profile">
    <EmptyState
      v-if="!company"
      icon="🎯" title="尚未选择公司"
      desc="请先在「公司查询」中检索并点击一家公司, 或直接使用顶栏右侧的公司选择器。"
      action-text="前往公司查询" @action="emit('navigate', 'list')"
    />

    <template v-else>
      <!-- 公司总览 -->
      <div class="card overview">
        <div class="ov-left">
          <div class="ov-title">
            <h2>{{ company.stockName }}</h2>
            <span class="mono ov-code">{{ company.stockCode }}</span>
            <span class="tag mute">{{ company.industryName || '—' }}</span>
            <span v-if="company.exchange" class="tag">{{ company.exchange === 'SH' ? '上交所' : '深交所' }}</span>
          </div>
          <div class="ov-sub muted">
            {{ company.fullName || '—' }}
            <template v-if="company.listDate"> · 上市日期 {{ company.listDate }}</template>
          </div>
          <div v-if="benchmark" class="ov-meta">
            <span>对标年度 <b>{{ year }}</b> 年报</span>
            <span class="sep">|</span>
            <span>行业样本 <b>{{ items.length ? items[0].total : '—' }}</b> 家</span>
            <span class="sep">|</span>
            <span>覆盖指标 <b>{{ items.length }}</b> 项</span>
          </div>
        </div>

        <div class="ov-score">
          <div class="score-ring" :style="{ '--pct': `${avgScore || 0}%`, '--clr': scoreColor(avgScore) }">
            <div class="ring-inner">
              <span class="ring-num">{{ avgScore === null ? '—' : fmtNum(avgScore, 1) }}</span>
              <span class="ring-lab">综合评分</span>
            </div>
          </div>
          <div class="score-side">
            <span class="tag tag--lg" :class="rating.cls">{{ rating.text }}</span>
            <span class="muted">六维指标方向调整评分均值</span>
            <span v-if="best.length" class="muted mini">优势: {{ best.map(b => b.indicatorName).join('、') }}</span>
            <span v-if="worst.length" class="muted mini">短板: {{ worst.map(b => b.indicatorName).join('、') }}</span>
          </div>
        </div>

        <div class="ov-actions no-print">
          <button class="btn" @click="goAi">🤖 生成 AI 解读</button>
          <button class="btn btn-ghost" :disabled="!items.length" @click="exportCsv">⤓ 导出对标 CSV</button>
          <button class="btn btn-ghost" :disabled="!trendRaw.length" @click="exportTrendCsv">⤓ 导出趋势 CSV</button>
          <button class="btn btn-ghost" @click="doPrint">🖨️ 打印 / 存 PDF</button>
        </div>
      </div>

      <p v-if="err" class="alert"><span>⛔</span><span>{{ err }}</span>
        <button class="btn btn-ghost btn-xs" style="margin-left:auto" @click="load">重试</button>
      </p>

      <!-- 关键指标卡 -->
      <div class="kpi-grid">
        <StatCard
          v-for="[code, label, hint] in KPIS" :key="code"
          :label="label" :hint="hint"
          :value="pick(code) ? fmtNum(pick(code).companyValue) : '—'"
          :unit="pick(code) ? pick(code).unit : ''"
          :trend="pick(code) && pick(code).rank ? `行业第 ${pick(code).rank}/${pick(code).total}` : ''"
          :trend-tone="pick(code) && pick(code).score >= 55 ? 'ok' : 'warn'"
          :accent="pick(code) && pick(code).score >= 55 ? 'brand' : 'warn'"
        />
      </div>

      <!-- 雷达 + 趋势 -->
      <div class="grid-2">
        <div class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">🕸️</span>六维能力雷达</div>
            <span class="card-sub">维度内指标评分均值, 50 分为行业中位水平</span>
          </div>
          <EChart :option="radarOption" height="352px" :loading="loading" :empty="!dimScores.length" filename="六维能力雷达" />
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">📈</span>核心指标趋势</div>
            <span class="card-sub">{{ yearRange[0] }}–{{ yearRange[1] }} 年</span>
          </div>
          <div class="chips">
            <button
              v-for="[code, label] in TREND_CHOICES" :key="code"
              class="chip" :class="{ on: trendCodes.includes(code) }"
              @click="toggleTrend(code)"
            >{{ label }}</button>
          </div>
          <div class="mt-3">
            <EChart :option="trendOption" height="248px" :loading="loading" :empty="!trendRaw.length" filename="核心指标趋势" />
          </div>
          <p class="muted mt-2">提示: 不同指标量纲不同, 同图对比主要用于观察<strong>变化趋势</strong>; 各指标单位见提示框。</p>
        </div>
      </div>

      <!-- 行业对标图 -->
      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico">🎯</span>行业对标评分</div>
          <span class="card-sub">
            {{ year }} 年报 · {{ items.length ? items[0].total : '—' }} 家同行业样本
          </span>
          <div class="card-tools">
            <span class="tag ok">≥75 优</span>
            <span class="tag">55–75 良</span>
            <span class="tag warn">35–55 中</span>
            <span class="tag bad">&lt;35 弱</span>
          </div>
        </div>
        <EChart :option="benchOption" height="380px" :loading="loading" :empty="!items.length" filename="行业对标评分" />
        <p class="muted mt-2">
          评分 = 原始百分位按指标方向调整(0–100, 越高越优); 例如资产负债率为"越低越好", 其评分 = 100 − 原始百分位。
        </p>
      </div>

      <!-- 指标速览 -->
      <div class="card" v-if="items.length">
        <div class="card-hd">
          <div class="card-title"><span class="ico">🧾</span>指标速览</div>
          <span class="card-sub">按维度分组, 展示本公司值 / 行业中位数 / 行业排名</span>
        </div>
        <div class="dim-groups">
          <div v-for="dim in DIMENSIONS" :key="dim" class="dim-group">
            <template v-if="items.filter(i => i.dimension === dim).length">
              <div class="dg-title">{{ dim }}</div>
              <div class="tiles">
                <div v-for="it in items.filter(i => i.dimension === dim)" :key="it.indicatorCode" class="tile">
                  <div class="tile-head">
                    <IndicatorTip class="tile-name" :code="it.indicatorCode" :name="it.indicatorName" dense />
                    <span class="tag" :class="scoreLevel(it.score).cls">{{ scoreLevel(it.score).text }}</span>
                  </div>
                  <div class="tile-value">
                    <span class="mono tv-num">{{ fmtNum(it.companyValue) }}</span>
                    <span class="tv-unit">{{ it.unit }}</span>
                  </div>
                  <div class="tile-foot">
                    <span class="muted">中位 {{ fmtNum(it.medianValue) }}</span>
                    <span class="muted">排名 {{ it.rank }}/{{ it.total }}</span>
                  </div>
                  <div class="bar thin"><i :style="{ width: `${Math.max(2, Number(it.score) || 0)}%`, background: scoreColor(it.score) }"></i></div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 对标明细表 -->
      <div class="card" v-if="items.length">
        <div class="card-hd">
          <div class="card-title"><span class="ico">📋</span>行业对标明细</div>
          <span class="card-sub">点击表头可排序</span>
        </div>
        <div class="tbl-wrap">
          <table class="tbl">
            <thead>
              <tr>
                <th class="sortable" @click="sortBy('indicatorName')">指标 <span class="arrow">{{ arrow('indicatorName') }}</span></th>
                <th style="width:92px">维度</th>
                <th class="num sortable" @click="sortBy('companyValue')">本公司值 <span class="arrow">{{ arrow('companyValue') }}</span></th>
                <th class="num sortable" @click="sortBy('medianValue')">行业中位数 <span class="arrow">{{ arrow('medianValue') }}</span></th>
                <th class="num hide-sm">行业均值</th>
                <th class="num hide-sm">P25</th>
                <th class="num hide-sm">P75</th>
                <th class="num sortable" style="width:132px" @click="sortBy('percentile')">原始百分位 <span class="arrow">{{ arrow('percentile') }}</span></th>
                <th class="num sortable" style="width:120px" @click="sortBy('score')">评分 <span class="arrow">{{ arrow('score') }}</span></th>
                <th class="num sortable" style="width:96px" @click="sortBy('rank')">行业排名 <span class="arrow">{{ arrow('rank') }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in sortedItems" :key="it.indicatorCode">
                <td>
                  <div class="ind-cell">
                    <IndicatorTip :code="it.indicatorCode" :name="it.indicatorName" dense />
                    <span class="muted tiny">{{ directionText(it.betterDirection) }}</span>
                  </div>
                </td>
                <td><span class="tag mute">{{ it.dimension }}</span></td>
                <td class="num"><b>{{ fmtNum(it.companyValue) }}</b> <span class="muted">{{ it.unit }}</span></td>
                <td class="num">{{ fmtNum(it.medianValue) }}</td>
                <td class="num hide-sm">{{ fmtNum(it.avgValue) }}</td>
                <td class="num hide-sm">{{ fmtNum(it.p25) }}</td>
                <td class="num hide-sm">{{ fmtNum(it.p75) }}</td>
                <td class="num">
                  <div class="pct-cell">
                    <div class="rankbar"><i :style="{ left: `${Math.min(100, Math.max(0, Number(it.percentile) || 0))}%` }"></i></div>
                    <span class="mono">{{ fmtNum(it.percentile) }}</span>
                  </div>
                </td>
                <td class="num">
                  <span class="tag" :class="scoreLevel(it.score).cls">{{ scoreLevel(it.score).text }} {{ fmtNum(it.score) }}</span>
                </td>
                <td class="num mono">{{ it.rank }}<span class="muted">/{{ it.total }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 报表科目 -->
      <div class="card" v-if="profile">
        <div class="card-hd">
          <div class="card-title"><span class="ico">📑</span>财报原始科目</div>
          <span class="card-sub">{{ year }} 年报 · 共 {{ (profile.items || []).length }} 项</span>
          <div class="card-tools">
            <span v-if="profile.valuation" class="tag">收盘价 {{ fmtNum(profile.valuation.closePrice) }} 元/股</span>
            <span v-if="profile.valuation" class="tag purple">总市值 {{ fmtYi(profile.valuation.marketCap) }}</span>
          </div>
        </div>
        <div class="report-groups">
          <div v-for="g in reportGroups" :key="g.type" class="report-group">
            <div class="rg-title">{{ g.type }}</div>
            <table class="tbl">
              <thead><tr><th>科目</th><th class="num" style="width:190px">金额</th><th style="width:120px" class="hide-sm">相对量级</th></tr></thead>
              <tbody>
                <tr v-for="it in g.list" :key="it.itemCode">
                  <td>{{ it.itemName }}</td>
                  <td class="num mono">{{ fmtMoney(it.amount) }}</td>
                  <td class="hide-sm">
                    <div class="bar thin"><i :style="{ width: `${it.pct}%` }"></i></div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile { display: flex; flex-direction: column; gap: var(--sp-5); }

/* 总览 */
.overview { display: flex; align-items: center; gap: var(--sp-6); flex-wrap: wrap; }
.ov-left { flex: 1 1 340px; min-width: 0; }
.ov-title { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.ov-title h2 { font-size: 21px; color: var(--c-brand-800); }
.ov-code { font-size: 13px; color: var(--c-text-3); }
.ov-sub { margin-top: 5px; font-size: 12.5px; }
.ov-meta { margin-top: 10px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 12.5px; color: var(--c-text-2); }
.ov-meta b { color: var(--c-brand-700); }
.sep { color: var(--c-border-2); }

.ov-score { display: flex; align-items: center; gap: var(--sp-4); }
.score-ring {
  position: relative; width: 104px; height: 104px; flex: none; border-radius: 50%;
  background: conic-gradient(var(--clr) var(--pct), #e9eef5 0);
  display: grid; place-items: center;
}
.score-ring::after { content: ''; position: absolute; inset: 9px; background: #fff; border-radius: 50%; }
.ring-inner { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; line-height: 1.25; }
.ring-num { font-family: var(--font-num); font-size: 23px; font-weight: 700; color: var(--c-brand-800); }
.ring-lab { font-size: 11px; color: var(--c-text-3); }
.score-side { display: flex; flex-direction: column; gap: 5px; align-items: flex-start; }
.score-side .mini { font-size: 11.5px; max-width: 260px; }

.ov-actions { display: flex; flex-direction: column; gap: 8px; margin-left: auto; }
.ov-actions .btn { justify-content: flex-start; }

/* 栅格 */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(196px, 1fr)); gap: var(--sp-4); }
.grid-2 { display: grid; grid-template-columns: minmax(340px, 1fr) minmax(0, 1.55fr); gap: var(--sp-5); align-items: start; }

/* 芯片 */
.chips { display: flex; flex-wrap: wrap; gap: 6px; }

/* 指标速览 */
.dim-groups { display: flex; flex-direction: column; gap: var(--sp-4); }
.dim-group { display: flex; flex-direction: column; gap: 8px; }
.dg-title { font-size: 12.5px; font-weight: 600; color: var(--c-brand-700); padding-left: 9px; border-left: 3px solid var(--c-brand-400); }
.tiles { display: grid; grid-template-columns: repeat(auto-fill, minmax(228px, 1fr)); gap: var(--sp-3); }
.tile { padding: 10px 12px; background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md); display: flex; flex-direction: column; gap: 6px; }
.tile-head { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
.tile-name { font-size: 12.5px; color: var(--c-text-2); }
.tile-value { display: flex; align-items: baseline; gap: 3px; }
.tv-num { font-size: 18px; font-weight: 700; color: var(--c-brand-800); }
.tv-unit { font-size: 11.5px; color: var(--c-text-3); }
.tile-foot { display: flex; justify-content: space-between; font-size: 11.5px; }

/* 明细表 */
.ind-cell { display: flex; flex-direction: column; }
.tiny { font-size: 11px; }
.pct-cell { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.pct-cell .rankbar { flex: none; }

/* 报表分组 */
.report-groups { display: flex; flex-direction: column; gap: var(--sp-5); }
.rg-title { font-size: 12.5px; font-weight: 600; color: var(--c-brand-700); margin-bottom: 6px; padding-left: 9px; border-left: 3px solid var(--c-brand-300); }

@media (max-width: 1080px) {
  .grid-2 { grid-template-columns: 1fr; }
  .ov-actions { flex-direction: row; flex-wrap: wrap; margin-left: 0; width: 100%; }
}
</style>
