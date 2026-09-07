<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { api, fmtNum, fmtYi, YEARS } from '../api'
import EChart from './EChart.vue'

const props = defineProps({ company: Object })
const year = ref(2025)

const loading = ref(false)
const err = ref('')
const profile = ref(null)
const benchmark = ref(null)
const trendRaw = ref([])          // [{indicatorCode, indicatorName, unit, points:[{year,value}]}]
const trendCodes = ref(['roe', 'revenue_growth', 'asset_liability_ratio'])

const TREND_CHOICES = [
  ['roe', 'ROE'], ['gross_margin', '毛利率'], ['net_margin_parent', '归母净利率'],
  ['revenue_growth', '营收增速'], ['profit_growth', '净利增速'],
  ['asset_liability_ratio', '资产负债率'], ['current_ratio', '流动比率'], ['cashflow_quality', '现金流/净利']
]

function toggleTrend(code) {
  const i = trendCodes.value.indexOf(code)
  if (i >= 0) trendCodes.value = trendCodes.value.filter(c => c !== code)
  else trendCodes.value = [...trendCodes.value, code]
}

async function load() {
  if (!props.company) return
  loading.value = true
  err.value = ''
  try {
    const [p, b, t] = await Promise.all([
      api.profile(props.company.companyId, year.value),
      api.benchmark(props.company.companyId, year.value),
      api.trend(props.company.companyId)
    ])
    profile.value = p
    benchmark.value = b
    trendRaw.value = t
  } catch (e) {
    err.value = e.message
    profile.value = null
    benchmark.value = null
    trendRaw.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.company, load)
watch(year, load)
onMounted(load)

// ---------- 图表 option ----------
const trendOption = computed(() => {
  const years = YEARS
  const chosen = trendCodes.value
  const series = trendRaw.value
    .filter(t => chosen.includes(t.indicatorCode))
    .map(t => ({
      name: t.indicatorName,
      type: 'line',
      smooth: true,
      connectNulls: true,
      symbolSize: 7,
      data: years.map(y => {
        const pt = (t.points || []).find(p => p.year === y)
        return pt ? pt.value : null
      })
    }))
  return {
    color: ['#1f3b63', '#2e86de', '#20bf6b', '#e67e22', '#8e44ad', '#d63031'],
    tooltip: { trigger: 'axis' },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 55, right: 20, top: 40, bottom: 30 },
    xAxis: { type: 'category', boundaryGap: false, data: years.map(y => y + '年') },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { type: 'dashed' } } },
    series
  }
})

// 行业对标: 评分 vs 原始百分位(同量纲 0-100, 可横比)
const benchOption = computed(() => {
  const items = (benchmark.value && benchmark.value.items) || []
  const sorted = [...items].sort((a, b) => (a.score || 0) - (b.score || 0))
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const it = sorted[params[0].dataIndex]
        return [
          `${it.indicatorName}(${it.dimension})`,
          `公司值: ${fmtNum(it.companyValue)} ${it.unit}`,
          `行业中位数: ${fmtNum(it.medianValue)}`,
          `P25: ${fmtNum(it.p25)} | P75: ${fmtNum(it.p75)}`,
          `行业排名: ${it.rank}/${it.total}`
        ].join('<br/>')
      }
    },
    legend: { top: 0 },
    grid: { left: 8, right: 70, top: 34, bottom: 8, containLabel: true },
    xAxis: { type: 'value', min: 0, max: 100 },
    yAxis: { type: 'category', data: sorted.map(i => i.indicatorName), axisLabel: { fontSize: 11 } },
    series: [
      {
        name: '评分(方向调整)', type: 'bar', barWidth: 7,
        data: sorted.map(it => ({
          value: it.score == null ? null : Number(it.score),
          itemStyle: { color: (it.score || 0) >= 55 ? '#1e7e34' : (it.score || 0) >= 35 ? '#e67e22' : '#c0392b' }
        })),
        label: { show: true, position: 'right', fontSize: 10, formatter: p => fmtNum(p.value) }
      },
      {
        name: '原始百分位', type: 'bar', barWidth: 7,
        data: sorted.map(it => it.percentile == null ? null : Number(it.percentile)),
        itemStyle: { color: '#b9c7da' }
      }
    ]
  }
})

function scoreTag(score) {
  if (score === null || score === undefined) return ''
  if (score >= 75) return '优'
  if (score >= 55) return '良'
  if (score >= 35) return '中'
  return '弱'
}
</script>

<template>
  <div v-if="!company" class="card muted">请先在「公司查询 / 行业排行 / 智能筛选」中选择一家公司。</div>

  <div v-else>
    <div class="card">
      <div class="row">
        <h2 style="font-size:18px;color:#1f3b63">
          {{ company.stockName }} <span class="muted">{{ company.stockCode }} · {{ company.industryName || '—' }}</span>
        </h2>
        <label class="muted" style="margin-left:auto">财年
          <select v-model.number="year">
            <option v-for="y in YEARS" :key="y" :value="y">{{ y }} 年报</option>
          </select>
        </label>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
      <p v-if="loading" class="muted mt">加载中…</p>
    </div>

    <!-- 估值摘要 -->
    <div class="card mt" v-if="profile && profile.valuation">
      <div class="row">
        <span class="kv">估值快照({{ fmtNum(profile.valuation.closePrice) }} 元 / 股)</span>
        <span class="tag">总市值 {{ fmtYi(profile.valuation.marketCap) }}</span>
      </div>
    </div>

    <!-- 指标趋势图 -->
    <div class="card mt">
      <div class="row" style="justify-content: space-between">
        <h3>📈 核心指标趋势(2021–2025)</h3>
      </div>
      <div class="row mt chips">
        <button v-for="[code, label] in TREND_CHOICES" :key="code" class="chip"
                :class="{ on: trendCodes.includes(code) }" @click="toggleTrend(code)">
          {{ label }}
        </button>
      </div>
      <div class="mt" v-if="trendRaw.length">
        <EChart :option="trendOption" height="320px" />
      </div>
      <p v-else class="muted mt">暂无趋势数据</p>
    </div>

    <!-- 行业对标图 -->
    <div class="card mt" v-if="benchmark && benchmark.items.length">
      <h3>🎯 行业对标评分({{ year }} 年 · 同行业 {{ benchmark.items[0].total }} 家样本)</h3>
      <div class="mt"><EChart :option="benchOption" height="360px" /></div>
      <p class="muted mt">评分 = 原始百分位按指标方向调整(0–100, 越高越优); 点击图例可切换对比「评分 / 原始百分位」</p>
    </div>

    <!-- 行业对标明细表 -->
    <div class="card mt" v-if="benchmark && benchmark.items.length">
      <h3>行业对标明细({{ year }} 年)</h3>
      <table class="mt">
        <thead>
          <tr>
            <th>指标</th><th>维度</th><th class="num">公司值</th><th class="num">行业中位数</th>
            <th class="num">行业均值</th><th class="num">P25</th><th class="num">P75</th>
            <th class="num">百分位</th><th class="num">评分</th><th class="num">排名</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="it in benchmark.items" :key="it.indicatorCode">
            <td>{{ it.indicatorName }}</td>
            <td>{{ it.dimension }}</td>
            <td class="num">{{ fmtNum(it.companyValue) }} <span class="muted">{{ it.unit }}</span></td>
            <td class="num">{{ fmtNum(it.medianValue) }}</td>
            <td class="num">{{ fmtNum(it.avgValue) }}</td>
            <td class="num">{{ fmtNum(it.p25) }}</td>
            <td class="num">{{ fmtNum(it.p75) }}</td>
            <td class="num">{{ fmtNum(it.percentile) }}</td>
            <td class="num">
              <span class="tag" :class="(it.score || 0) >= 55 ? 'ok' : 'warn'">
                {{ scoreTag(it.score) }} {{ fmtNum(it.score) }}
              </span>
            </td>
            <td class="num">{{ it.rank }}/{{ it.total }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 财务画像原始数据 -->
    <div class="card mt" v-if="profile">
      <h3>财务画像 · 报表科目({{ year }} 年)</h3>
      <table class="mt">
        <thead><tr><th>科目</th><th>报表</th><th class="num">金额</th></tr></thead>
        <tbody>
          <tr v-for="it in profile.items" :key="it.itemCode">
            <td>{{ it.itemName }}</td>
            <td>{{ it.reportType }}</td>
            <td class="num">{{ fmtYi(it.amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.chips { gap: 6px; }
button.chip {
  background: #eef2f8; color: #445; font-size: 13px; padding: 4px 10px;
  border-radius: 14px; border: 1px solid #d5dde8;
}
button.chip.on { background: #1f3b63; color: #fff; border-color: #1f3b63; }
.kv { font-size: 14px; color: #333; font-weight: 600; }
</style>
