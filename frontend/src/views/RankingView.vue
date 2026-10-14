<script setup>
/** 行业排行: 同行业同财年按指定指标横向排名(领奖台 + 分布图 + 明细表) */
import { ref, computed, watch, onMounted } from 'vue'
import { api, DIMENSIONS } from '../api'
import { store, toast, bootstrap } from '../store'
import EChart from '../components/EChart.vue'
import EmptyState from '../components/EmptyState.vue'
import SkeletonTable from '../components/SkeletonTable.vue'
import IndicatorTip from '../components/IndicatorTip.vue'
import { categoryAxis, valueAxis, tooltip, emptyOption } from '../utils/charts'
import { fmtNum, directionText, downloadCsv } from '../utils/format'

const emit = defineEmits(['select', 'navigate'])

const industryId = ref('')
const code = ref('roe')
const rows = ref([])
const loading = ref(false)
const err = ref('')

const year = computed(() => store.year)
const meta = computed(() => store.indicatorMap.get(code.value) || null)

const MEDAL = ['🥇', '🥈', '🥉']
const RANK_COLOR = ['#e2a134', '#93a3b8', '#c98a5b']

const top3 = computed(() => rows.value.slice(0, 3))

const stats = computed(() => {
  const vals = rows.value.map(r => Number(r.value)).filter(Number.isFinite).sort((a, b) => a - b)
  if (!vals.length) return null
  const q = (p) => {
    const pos = (vals.length - 1) * p
    const lo = Math.floor(pos), hi = Math.ceil(pos)
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)
  }
  return {
    count: vals.length,
    min: vals[0],
    max: vals[vals.length - 1],
    median: q(0.5),
    p25: q(0.25),
    p75: q(0.75),
    avg: vals.reduce((a, b) => a + b, 0) / vals.length
  }
})

async function load() {
  if (!industryId.value || !code.value) return
  loading.value = true
  err.value = ''
  try {
    const data = await api.ranking({
      industryId: industryId.value,
      fiscalYear: year.value,
      indicatorCode: code.value
    })
    rows.value = [...(data || [])].sort((a, b) => (a.rank || 999) - (b.rank || 999))
  } catch (e) {
    err.value = e.message
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // 兼容直接进入本页(或刷新)时字典尚未就绪的情况
  if (!store.industries.length) await bootstrap()
  if (!industryId.value && store.industries.length) industryId.value = store.industries[0].industryId
  load()
})

watch([industryId, code], load)
watch(year, () => { toast(`财年已切换为 ${year.value}, 重新排名`, 'info', 1800); load() })

const barOption = computed(() => {
  if (!rows.value.length) return emptyOption('该行业 / 年度暂无此指标数据')
  const list = [...rows.value].reverse()   // y 轴自下而上, 让第 1 名在最上方
  return {
    tooltip: tooltip({
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(ps) {
        const r = list[ps[0].dataIndex]
        return `<b>${r.stockName}</b> <span style="color:#8a97a8">${r.stockCode}</span><br/>`
          + `${meta.value ? meta.value.name : code.value}: <b>${fmtNum(r.value)}</b> ${meta.value ? meta.value.unit : ''}<br/>`
          + `行业排名: 第 ${r.rank} / ${rows.value.length} 名 ｜ 百分位: ${fmtNum(r.percentile)}`
      }
    }),
    grid: { left: 8, right: 68, top: 12, bottom: 6, containLabel: true },
    xAxis: valueAxis({ name: meta.value ? meta.value.unit : '', nameGap: 18, nameLocation: 'end' }),
    yAxis: categoryAxis(list.map(r => r.stockName), {
      axisLabel: { fontSize: 11.5, color: '#52637a' },
      axisLine: { show: false }
    }),
    series: [{
      type: 'bar',
      barWidth: 13,
      data: list.map(r => ({
        value: Number(r.value),
        itemStyle: {
          borderRadius: [0, 5, 5, 0],
          color: r.rank <= 3 ? RANK_COLOR[r.rank - 1] : '#4a89e0'
        }
      })),
      label: {
        show: true, position: 'right', fontSize: 11, color: '#52637a',
        formatter: p => fmtNum(p.value, 2)
      }
    }]
  }
})

function exportCsv() {
  if (!rows.value.length) return
  const headers = ['排名', '股票代码', '股票简称', meta.value ? meta.value.name : code.value, '单位', '原始百分位']
  const data = rows.value.map(r => [r.rank, r.stockCode, r.stockName, r.value, meta.value ? meta.value.unit : '', r.percentile])
  const ind = store.industryMap.get(Number(industryId.value))
  const name = `${ind ? ind.industryName : ''}_${year.value}_${meta.value ? meta.value.name : code.value}_排行.csv`
  downloadCsv(name, headers, data)
  toast(`已导出 ${name}`, 'ok')
}

const pick = (r) => emit('select', { companyId: r.companyId, stockCode: r.stockCode, stockName: r.stockName, industryId: Number(industryId.value) })
</script>

<template>
  <div class="ranking">
    <!-- 筛选 -->
    <div class="card">
      <div class="card-hd">
        <div class="card-title"><span class="ico">🏆</span>行业指标排行</div>
        <span class="card-sub">同行业 · 同财年 · 按单一指标横向对比, 排名 1 = 最优</span>
        <div class="card-tools">
          <button class="btn btn-ghost btn-sm" :disabled="!rows.length" @click="exportCsv">⤓ 导出 CSV</button>
        </div>
      </div>

      <div class="filter-bar card-bd">
        <div class="field">
          <span class="field-label">行业范围</span>
          <select v-model="industryId" style="min-width:280px">
            <option v-for="i in store.industries" :key="i.industryId" :value="i.industryId">
              {{ i.industryName }}({{ i.companyCount }}家)
            </option>
          </select>
        </div>
        <div class="field">
          <span class="field-label">排名指标</span>
          <select v-model="code" style="min-width:240px">
            <optgroup v-for="dim in DIMENSIONS" :key="dim" :label="dim">
              <option v-for="m in store.indicators.filter(i => i.dimension === dim)" :key="m.code" :value="m.code">{{ m.name }}</option>
            </optgroup>
          </select>
        </div>
        <div class="field">
          <span class="field-label">财年</span>
          <input :value="`${year} 年报`" disabled style="width:110px" />
        </div>
        <div v-if="meta" class="meta-hint">
          <IndicatorTip :code="code" :name="meta.name" dense />
          <span class="tag">单位 {{ meta.unit }}</span>
          <span class="tag" :class="meta.betterDirection === 'higher_better' ? 'ok' : 'warn'">
            {{ meta.betterDirection === 'higher_better' ? '↑' : '↓' }} {{ directionText(meta.betterDirection) }}
          </span>
          <span class="muted">{{ meta.dimension }}</span>
        </div>
      </div>
      <p v-if="err" class="alert mt-3"><span>⛔</span><span>{{ err }}</span>
        <button class="btn btn-ghost btn-xs" style="margin-left:auto" @click="load">重试</button>
      </p>
    </div>

    <SkeletonTable v-if="loading" :rows="6" :cols="4" />

    <template v-else-if="rows.length">
      <!-- Top3 领奖台 -->
      <div class="podium">
        <div v-for="(r, i) in top3" :key="r.companyId" class="pod" :class="`pod-${i + 1}`">
          <div class="pod-rank">{{ MEDAL[i] }}</div>
          <div class="pod-name">{{ r.stockName }}</div>
          <div class="pod-code mono">{{ r.stockCode }}</div>
          <div class="pod-value">
            <span class="mono">{{ fmtNum(r.value) }}</span>
            <span class="pod-unit">{{ meta ? meta.unit : '' }}</span>
          </div>
          <div class="pod-meta muted">百分位 {{ fmtNum(r.percentile) }}</div>
          <button class="btn btn-ghost btn-xs" @click="pick(r)">查看画像 →</button>
        </div>
      </div>

      <!-- 分布摘要 -->
      <div v-if="stats" class="stat-strip">
        <div class="ss-item"><span class="ss-k">样本数</span><span class="ss-v">{{ stats.count }} 家</span></div>
        <div class="ss-item"><span class="ss-k">最高</span><span class="ss-v text-up">{{ fmtNum(stats.max) }}</span></div>
        <div class="ss-item"><span class="ss-k">P75</span><span class="ss-v">{{ fmtNum(stats.p75) }}</span></div>
        <div class="ss-item"><span class="ss-k">中位数</span><span class="ss-v">{{ fmtNum(stats.median) }}</span></div>
        <div class="ss-item"><span class="ss-k">P25</span><span class="ss-v">{{ fmtNum(stats.p25) }}</span></div>
        <div class="ss-item"><span class="ss-k">最低</span><span class="ss-v text-down">{{ fmtNum(stats.min) }}</span></div>
        <div class="ss-item"><span class="ss-k">单位</span><span class="ss-v">{{ meta ? meta.unit : '—' }}</span></div>
      </div>

      <!-- 分布图 -->
      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico">📊</span>{{ meta ? meta.name : code }} · 行业分布</div>
          <span class="card-sub">{{ year }} 年报 · 共 {{ rows.length }} 家样本</span>
          <div class="card-tools">
            <span class="tag" style="background:#f6e7c8;color:#a3741a">🥇 第 1 名</span>
            <span class="tag mute">🥈🥉 前三名</span>
          </div>
        </div>
        <EChart :option="barOption" height="360px" :filename="`${code}_行业分布`" />
      </div>

      <!-- 明细表 -->
      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico">📋</span>排行明细</div>
          <span class="card-sub">点击行可载入该公司</span>
        </div>
        <div class="tbl-wrap">
          <table class="tbl">
            <thead>
              <tr>
                <th style="width:76px" class="center">排名</th>
                <th style="width:104px">股票代码</th>
                <th style="width:120px">股票简称</th>
                <th class="num">{{ meta ? meta.name : code }}</th>
                <th class="num" style="width:120px">原始百分位</th>
                <th style="width:150px">相对水平</th>
                <th class="center" style="width:110px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in rows" :key="r.companyId" class="clickable"
                :class="{ 'is-active': store.selectedCompany && store.selectedCompany.companyId === r.companyId }"
                @click="pick(r)"
              >
                <td class="center">
                  <span v-if="r.rank <= 3" class="medal">{{ MEDAL[r.rank - 1] }}</span>
                  <span class="mono">{{ r.rank }}</span>
                </td>
                <td class="mono">{{ r.stockCode }}</td>
                <td><b>{{ r.stockName }}</b></td>
                <td class="num"><b>{{ fmtNum(r.value) }}</b> <span class="muted">{{ meta ? meta.unit : '' }}</span></td>
                <td class="num mono">{{ fmtNum(r.percentile) }}</td>
                <td>
                  <div class="bar"><i :style="{ width: `${Math.min(100, Math.max(0, Number(r.percentile) || 0))}%` }"></i></div>
                </td>
                <td class="center">
                  <button class="btn btn-ghost btn-xs" @click.stop="pick(r)">查看画像 →</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else-if="!loading && !err" class="card">
      <EmptyState
        icon="🏆" title="该行业 / 年度暂无此指标数据"
        desc="可尝试切换其他指标或财年; 若全部为空, 请确认后端已执行过一次指标重算(POST /api/finance/recalc)。"
      />
    </div>
  </div>
</template>

<style scoped>
.ranking { display: flex; flex-direction: column; gap: var(--sp-5); }
.filter-bar { display: flex; gap: var(--sp-4); align-items: flex-end; flex-wrap: wrap; }
.meta-hint { display: flex; align-items: center; gap: 7px; margin-left: auto; flex-wrap: wrap; }

/* 领奖台 */
.podium { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: var(--sp-4); }
.pod {
  position: relative; display: flex; flex-direction: column; align-items: center; gap: 5px;
  padding: 18px 16px 16px; text-align: center;
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg);
  box-shadow: var(--sh-1); overflow: hidden;
}
.pod-1 { border-color: #eccf92; background: linear-gradient(180deg, #fffdf6, #fff); }
.pod-2 { border-color: #d6dee7; }
.pod-3 { border-color: #e4c8b0; }
.pod-rank { font-size: 26px; line-height: 1; }
.pod-name { font-size: 15.5px; font-weight: 700; color: var(--c-brand-800); }
.pod-code { font-size: 11.5px; color: var(--c-text-3); }
.pod-value { display: flex; align-items: baseline; gap: 3px; margin: 4px 0 1px; }
.pod-value .mono { font-size: 21px; font-weight: 700; color: var(--c-brand-600); }
.pod-unit { font-size: 11.5px; color: var(--c-text-3); }
.pod-meta { font-size: 11.5px; }

/* 分布摘要 */
.stat-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 1px;
  background: var(--c-border); border: 1px solid var(--c-border);
  border-radius: var(--r-lg); overflow: hidden;
}
.ss-item { display: flex; flex-direction: column; gap: 2px; padding: 11px 14px; background: var(--c-surface); }
.ss-k { font-size: 11.5px; color: var(--c-text-3); }
.ss-v { font-family: var(--font-num); font-size: 15px; font-weight: 600; color: var(--c-brand-800); }

.medal { margin-right: 5px; }
</style>
