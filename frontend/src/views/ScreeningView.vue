<script setup>
/**
 * 智能筛选: 多条件 AND 交叉选股
 * 左侧为条件编辑器, 右侧为命中结果与逐条件判定明细
 */
import { ref, computed, watch, onMounted } from 'vue'
import { api, DIMENSIONS, OPERATORS } from '../api'
import { store, toast, bootstrap } from '../store'
import EmptyState from '../components/EmptyState.vue'
import { fmtNum, opText, downloadCsv } from '../utils/format'

defineOptions({ name: 'ScreeningView' })
const emit = defineEmits(['select', 'navigate'])

const industryId = ref('')
const conditions = ref([{ indicatorCode: 'roe', operator: 'gte', value: 15, value2: null }])
const result = ref(null)
const loading = ref(false)
const err = ref('')
const year = computed(() => store.year)

const MAX_COND = 6

const PRESETS = [
  {
    name: '白酒 · 高 ROE 低负债',
    industryId: 3,
    conditions: [
      { indicatorCode: 'roe', operator: 'gte', value: 20, value2: null },
      { indicatorCode: 'asset_liability_ratio', operator: 'lte', value: 40, value2: null }
    ]
  },
  {
    name: '医药 · 高毛利 + 高成长',
    industryId: 2,
    conditions: [
      { indicatorCode: 'gross_margin', operator: 'gte', value: 50, value2: null },
      { indicatorCode: 'revenue_growth', operator: 'gte', value: 8, value2: null }
    ]
  },
  {
    name: '全市场 · 低估值 + 盈利尚可',
    industryId: '',
    conditions: [
      { indicatorCode: 'pe', operator: 'lte', value: 30, value2: null },
      { indicatorCode: 'roe', operator: 'gte', value: 12, value2: null }
    ]
  },
  {
    name: '全市场 · 行业前 30% 盈利',
    industryId: '',
    conditions: [
      { indicatorCode: 'roe', operator: 'pct_gt', value: 70, value2: null }
    ]
  }
]

const metaOf = (code) => store.indicatorMap.get(code) || null
const isPct = (op) => String(op).startsWith('pct_')

function addCondition() {
  if (conditions.value.length >= MAX_COND) { toast(`最多 ${MAX_COND} 个条件`, 'warn'); return }
  conditions.value.push({ indicatorCode: 'roe', operator: 'gte', value: null, value2: null })
}
function removeCondition(i) {
  if (conditions.value.length === 1) { toast('至少保留一个条件', 'warn'); return }
  conditions.value.splice(i, 1)
}
function clearAll() {
  conditions.value = [{ indicatorCode: 'roe', operator: 'gte', value: null, value2: null }]
  result.value = null
}

function applyPreset(p) {
  industryId.value = p.industryId
  conditions.value = p.conditions.map(c => ({ ...c }))
  run()
}

const clean = (v) => (v === '' || v === null || v === undefined || Number.isNaN(Number(v))) ? null : Number(v)

async function run() {
  const conds = conditions.value
    .map(c => {
      const o = { indicatorCode: c.indicatorCode, operator: c.operator, value: clean(c.value) }
      if (c.operator === 'between') o.value2 = clean(c.value2)
      return o
    })
    .filter(c => c.indicatorCode && c.operator && c.value !== null && (c.operator !== 'between' || c.value2 !== null))

  if (!conds.length) { err.value = '请至少填写一个有效条件(条件需包含指标、运算符与阈值)'; result.value = null; return }

  const payload = { fiscalYear: year.value, reportPeriod: '年报', conditions: conds, page: 1, size: 100 }
  if (industryId.value) payload.industryId = Number(industryId.value)

  loading.value = true
  err.value = ''
  try {
    result.value = await api.screening(payload)
    if (!result.value.total) toast('没有公司同时满足全部条件, 可适当放宽阈值', 'warn', 3600)
    else toast(`命中 ${result.value.total} 家公司`, 'ok', 2200)
  } catch (e) {
    err.value = e.message
    result.value = null
  } finally {
    loading.value = false
  }
}

watch(year, () => {
  if (result.value) { toast(`财年已切换为 ${year.value}, 重新筛选`, 'info', 1800); run() }
})

onMounted(async () => {
  if (!store.industries.length) await bootstrap()
})

/** 条件摘要文案, 例如: ROE ≥ 15 且 资产负债率 ≤ 50 */
const conditionSummary = computed(() =>
  conditions.value
    .filter(c => c.indicatorCode && clean(c.value) !== null)
    .map(c => {
      const m = metaOf(c.indicatorCode)
      const unit = m ? m.unit : ''
      const v1 = fmtNum(clean(c.value))
      if (c.operator === 'between') return `${m ? m.name : c.indicatorCode} 介于 ${v1} ~ ${fmtNum(clean(c.value2))} ${unit}`
      if (isPct(c.operator)) return `${m ? m.name : c.indicatorCode} ${opText(c.operator)} ${v1}%`
      return `${m ? m.name : c.indicatorCode} ${opText(c.operator)} ${v1} ${unit}`
    })
)

function exportCsv() {
  if (!result.value || !result.value.companies) return
  const headers = ['股票代码', '股票简称', '所属行业', '命中条件数', '条件判定明细']
  const rows = result.value.companies.map(c => [
    c.stockCode, c.stockName, c.industryName, c.matchedCount,
    (c.details || []).map(d => `${d.indicatorName}${d.actualValue == null ? '—' : fmtNum(d.actualValue)} ${opText(d.operator)} ${fmtNum(d.value)}${d.value2 != null ? '~' + fmtNum(d.value2) : ''} [${d.passed ? '达标' : '未达标'}]`).join(' ; ')
  ])
  const name = `智能筛选结果_${year.value}年报_${result.value.total}家.csv`
  downloadCsv(name, headers, rows)
  toast(`已导出 ${name}`, 'ok')
}

const pick = (c) => emit('select', {
  companyId: c.companyId, stockCode: c.stockCode, stockName: c.stockName, industryName: c.industryName
})
</script>

<template>
  <div class="screening">
    <!-- 条件编辑器 -->
    <div class="card">
      <div class="card-hd">
        <div class="card-title"><span class="ico">🧮</span>智能筛选 · 多条件交叉(AND)</div>
        <span class="card-sub">全部条件同时满足才命中; 支持"高于/低于行业百分位"这类相对口径</span>
        <div class="card-tools">
          <button class="btn btn-ghost btn-sm" @click="clearAll">清空条件</button>
        </div>
      </div>

      <!-- 预设方案 -->
      <div class="preset-row">
        <span class="field-label">快速方案</span>
        <button v-for="p in PRESETS" :key="p.name" class="chip" @click="applyPreset(p)">🎯 {{ p.name }}</button>
      </div>

      <!-- 环境 -->
      <div class="env-row">
        <div class="field">
          <span class="field-label">筛选范围</span>
          <select v-model="industryId" style="min-width:250px">
            <option value="">全市场(全部行业)</option>
            <option v-for="i in store.industries" :key="i.industryId" :value="i.industryId">
              {{ i.industryName }}({{ i.companyCount }}家)
            </option>
          </select>
        </div>
        <div class="field">
          <span class="field-label">财年</span>
          <input :value="`${year} 年报`" disabled style="width:110px" />
        </div>
        <div class="field grow">
          <span class="field-label">条件预览</span>
          <div class="preview">
            <template v-if="conditionSummary.length">
              <span v-for="(s, i) in conditionSummary" :key="i" class="tag mute">{{ s }}</span>
            </template>
            <span v-else class="muted">尚未填写有效条件</span>
          </div>
        </div>
      </div>

      <!-- 条件列表 -->
      <div class="cond-list">
        <div v-for="(c, i) in conditions" :key="i" class="cond">
          <span class="cond-idx">{{ i + 1 }}</span>

          <select v-model="c.indicatorCode" style="min-width:220px">
            <optgroup v-for="dim in DIMENSIONS" :key="dim" :label="dim">
              <option v-for="m in store.indicators.filter(x => x.dimension === dim)" :key="m.code" :value="m.code">{{ m.name }}</option>
            </optgroup>
          </select>

          <select v-model="c.operator" style="min-width:158px">
            <option v-for="o in OPERATORS" :key="o.v" :value="o.v">{{ o.t }}</option>
          </select>

          <div class="val-box">
            <input
              v-model.number="c.value" type="number" step="any" style="width:112px"
              :placeholder="isPct(c.operator) ? '百分位 0–100' : '阈值'"
            />
            <span class="val-unit">{{ isPct(c.operator) ? '%' : (metaOf(c.indicatorCode) ? metaOf(c.indicatorCode).unit : '') }}</span>
          </div>

          <template v-if="c.operator === 'between'">
            <span class="tilde">~</span>
            <div class="val-box">
              <input v-model.number="c.value2" type="number" step="any" style="width:112px" placeholder="上限" />
              <span class="val-unit">{{ metaOf(c.indicatorCode) ? metaOf(c.indicatorCode).unit : '' }}</span>
            </div>
          </template>

          <span v-if="metaOf(c.indicatorCode)" class="cond-hint muted">
            {{ metaOf(c.indicatorCode).dimension }} · 单位 {{ metaOf(c.indicatorCode).unit }} ·
            {{ metaOf(c.indicatorCode).betterDirection === 'higher_better' ? '越高越好' : '越低越好' }}
          </span>

          <button class="btn btn-danger btn-xs cond-del" :disabled="conditions.length === 1" @click="removeCondition(i)">删除</button>
        </div>
      </div>

      <div class="run-row">
        <button class="btn btn-ghost" :disabled="conditions.length >= MAX_COND" @click="addCondition">
          ＋ 添加条件 ({{ conditions.length }}/{{ MAX_COND }})
        </button>
        <button class="btn" :disabled="loading" @click="run">
          {{ loading ? '筛选中…' : '🔍 开始筛选' }}
        </button>
        <span class="muted">运算符说明: ≥ / > / ≤ / < / 介于区间 / 高于或低于同行业同年度的百分位</span>
      </div>

      <p v-if="err" class="alert mt-3"><span>⛔</span><span>{{ err }}</span></p>
    </div>

    <!-- 结果 -->
    <div v-if="result" class="card">
      <div class="card-hd">
        <div class="card-title"><span class="ico">✅</span>筛选结果</div>
        <span class="card-sub">命中 {{ result.total }} 家公司 · 满足 {{ result.conditionCount }} 个条件 · {{ year }} 年报</span>
        <div class="card-tools">
          <button class="btn btn-ghost btn-sm" :disabled="!result.companies || !result.companies.length" @click="exportCsv">⤓ 导出 CSV</button>
        </div>
      </div>

      <EmptyState
        v-if="!result.companies || !result.companies.length"
        icon="🫙" title="没有公司同时满足全部条件"
        desc="可以尝试放宽阈值、减少条件数量, 或把范围从单行业改为全市场。"
      />

      <div v-else class="tbl-wrap">
        <table class="tbl">
          <thead>
            <tr>
              <th style="width:104px">股票代码</th>
              <th style="width:110px">股票简称</th>
              <th style="width:200px">所属行业</th>
              <th style="width:96px" class="center">命中条件</th>
              <th>条件判定明细</th>
              <th class="center" style="width:110px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="c in result.companies" :key="c.companyId"
              :class="{ 'is-active': store.selectedCompany && store.selectedCompany.companyId === c.companyId }"
            >
              <td class="mono">{{ c.stockCode }}</td>
              <td><b>{{ c.stockName }}</b></td>
              <td><span class="tag mute">{{ c.industryName }}</span></td>
              <td class="center">
                <span class="tag ok">{{ c.matchedCount }}/{{ (c.details || []).length }}</span>
              </td>
              <td>
                <div class="details">
                  <span
                    v-for="(d, j) in c.details" :key="j"
                    class="chip chip--static dt"
                    :class="d.passed ? 'pass' : 'fail'"
                  >
                    <span class="dt-ico">{{ d.passed ? '✓' : '✕' }}</span>
                    {{ d.indicatorName }}
                    <b class="mono">{{ d.actualValue === null || d.actualValue === undefined ? '—' : fmtNum(d.actualValue) }}</b>
                    <span class="dt-op">{{ opText(d.operator) }}</span>
                    <span class="mono">{{ fmtNum(d.value) }}<template v-if="d.value2 != null"> ~ {{ fmtNum(d.value2) }}</template></span>
                  </span>
                </div>
              </td>
              <td class="center">
                <button class="btn btn-ghost btn-xs" @click="pick(c)">查看画像 →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <p v-if="result.companies && result.companies.length" class="muted mt-3">
        💡 明细中 <span class="text-up">绿色 ✓</span> 表示该条件达标; 由于筛选为 AND 逻辑, 命中公司的条件应全部为达标状态。
      </p>
    </div>

    <div v-else-if="!loading" class="card">
      <EmptyState
        icon="🧮" title="设置条件后开始筛选"
        desc="示例: 范围选「白酒」, ROE ≥ 20 且 资产负债率 ≤ 40 —— 找出高盈利且低负债的公司, 再进入财务画像逐项核对。"
      />
    </div>
  </div>
</template>

<style scoped>
.screening { display: flex; flex-direction: column; gap: var(--sp-5); }

.preset-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding-bottom: var(--sp-3); }
.env-row { display: flex; gap: var(--sp-4); align-items: flex-end; flex-wrap: wrap; padding: var(--sp-3) 0 var(--sp-4); border-top: 1px dashed var(--c-border); }
.preview { display: flex; gap: 6px; flex-wrap: wrap; min-height: 36px; align-items: center; }

/* 条件行 */
.cond-list { display: flex; flex-direction: column; gap: 9px; }
.cond {
  display: flex; align-items: center; gap: 9px; flex-wrap: wrap;
  padding: 10px 12px 10px 34px; position: relative;
  background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md);
  transition: border-color var(--dur) var(--ease);
}
.cond:hover { border-color: var(--c-brand-300); }
.cond-idx {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  width: 18px; height: 18px; display: grid; place-items: center;
  font-size: 11px; font-weight: 700; color: var(--c-brand-600);
  background: var(--c-brand-100); border-radius: 50%;
}
.val-box { display: inline-flex; align-items: center; gap: 5px; }
.val-unit { font-size: 12px; color: var(--c-text-3); min-width: 28px; }
.tilde { color: var(--c-text-3); }
.cond-hint { font-size: 11.5px; flex: 1 1 190px; }
.cond-del { margin-left: auto; }

.run-row { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; margin-top: var(--sp-4); }

/* 结果明细 */
.details { display: flex; flex-wrap: wrap; gap: 5px; }
.dt { font-size: 11.5px; padding: 2px 9px; }
.dt.pass { background: var(--c-up-bg); color: var(--c-up); border-color: #c5e8d5; }
.dt.fail { background: var(--c-down-bg); color: var(--c-down); border-color: #f6cfd1; }
.dt-ico { font-weight: 700; }
.dt-op { color: var(--c-text-3); margin: 0 2px; }
</style>
