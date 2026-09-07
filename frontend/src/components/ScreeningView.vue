<script setup>
import { ref, onMounted } from 'vue'
import { api, fmtNum, YEARS } from '../api'

const emit = defineEmits(['select'])

const industries = ref([])
const indicators = ref([])
const metaMap = new Map()

const industryId = ref('')          // '' = 全市场
const year = ref(2025)
const conditions = ref([{ indicatorCode: 'roe', operator: 'gte', value: 15, value2: null }])
const result = ref(null)
const loading = ref(false)
const err = ref('')

const OPERATORS = [
  { v: 'gte', t: '≥' }, { v: 'gt', t: '>' },
  { v: 'lte', t: '≤' }, { v: 'lt', t: '<' },
  { v: 'between', t: '介于' },
  { v: 'pct_gt', t: '高于行业百分位' }, { v: 'pct_lt', t: '低于行业百分位' }
]
const opText = (op) => (OPERATORS.find(o => o.v === op) || {}).t || op

onMounted(async () => {
  try {
    const [is, inds] = await Promise.all([api.industries(), api.indicators()])
    industries.value = is
    indicators.value = inds
    inds.forEach(m => metaMap.set(m.code, m))
  } catch (e) { err.value = e.message }
})

function addCondition() {
  if (conditions.value.length >= 6) return
  conditions.value.push({ indicatorCode: 'roe', operator: 'gte', value: null, value2: null })
}
function removeCondition(i) { conditions.value.splice(i, 1) }

function loadExample() {
  industryId.value = 3
  year.value = 2025
  conditions.value = [
    { indicatorCode: 'roe', operator: 'gte', value: 10, value2: null },
    { indicatorCode: 'asset_liability_ratio', operator: 'lte', value: 50, value2: null }
  ]
  run()
}

function clean(v) { return (v === '' || v === null || v === undefined || Number.isNaN(v)) ? null : Number(v) }

async function run() {
  const conds = conditions.value
    .filter(c => c.indicatorCode && c.operator)
    .map(c => {
      const o = { indicatorCode: c.indicatorCode, operator: c.operator, value: clean(c.value) }
      if (c.operator === 'between') o.value2 = clean(c.value2)
      return o
    })
    .filter(c => c.value !== null && (c.operator !== 'between' || c.value2 !== null))
  if (!conds.length) { err.value = '请至少填写一个有效条件'; return }
  const payload = { fiscalYear: year.value, reportPeriod: '年报', conditions: conds, page: 1, size: 50 }
  if (industryId.value) payload.industryId = Number(industryId.value)
  loading.value = true
  err.value = ''
  try {
    result.value = await api.screening(payload)
  } catch (e) { err.value = e.message; result.value = null }
  finally { loading.value = false }
}

const byDim = (dim) => indicators.value.filter(i => i.dimension === dim)
</script>

<template>
  <div>
    <div class="card">
      <div class="row">
        <h2 style="font-size:18px;color:#1f3b63">🔍 智能筛选(多条件 AND)</h2>
        <button class="secondary" style="margin-left:auto" @click="loadExample">🎯 载入示例: 白酒「高 ROE + 低负债」</button>
      </div>
      <div class="row mt filterbar">
        <label class="muted">范围
          <select v-model="industryId">
            <option value="">全市场</option>
            <option v-for="i in industries" :key="i.industryId" :value="i.industryId">{{ i.industryName }}</option>
          </select>
        </label>
        <label class="muted">财年
          <select v-model.number="year">
            <option v-for="y in YEARS" :key="y" :value="y">{{ y }} 年报</option>
          </select>
        </label>
      </div>

      <!-- 条件编辑器 -->
      <div v-for="(c, i) in conditions" :key="i" class="cond mt">
        <select v-model="c.indicatorCode" style="min-width:210px">
          <optgroup v-for="dim in ['盈利能力','成长性','财务风险','盈利质量','每股指标','估值']" :key="dim" :label="dim">
            <option v-for="m in byDim(dim)" :key="m.code" :value="m.code">{{ m.name }}</option>
          </optgroup>
        </select>
        <select v-model="c.operator" style="min-width:150px">
          <option v-for="o in OPERATORS" :key="o.v" :value="o.v">{{ o.t }}</option>
        </select>
        <input v-model.number="c.value" type="number" step="any" style="width:110px"
               :placeholder="c.operator.startsWith('pct_') ? '0–100' : '数值'" />
        <input v-if="c.operator === 'between'" v-model.number="c.value2" type="number" step="any" style="width:110px" placeholder="上限" />
        <span class="muted" style="min-width:120px">
          {{ metaMap.get(c.indicatorCode) ? metaMap.get(c.indicatorCode).name : '' }}
          <template v-if="metaMap.get(c.indicatorCode)">单位: {{ metaMap.get(c.indicatorCode).unit }}</template>
        </span>
        <button class="danger mini" @click="removeCondition(i)" :disabled="conditions.length === 1">删除</button>
      </div>

      <div class="row mt">
        <button class="secondary" @click="addCondition">＋ 添加条件</button>
        <button @click="run" :disabled="loading">{{ loading ? '筛选中…' : '开始筛选' }}</button>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
      <p class="muted mt">💡 条件之间为 AND(同时满足);「高于/低于行业百分位」按同行业同年指标分布计算</p>
    </div>

    <!-- 结果 -->
    <div class="card mt" v-if="result">
      <h3>命中 {{ result.total }} 家公司({{ result.conditionCount }} 个条件)</h3>
      <table class="mt">
        <thead>
          <tr><th>股票代码</th><th>股票简称</th><th>行业</th><th>条件判定明细</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in result.companies" :key="c.companyId">
            <td>{{ c.stockCode }}</td>
            <td>{{ c.stockName }}</td>
            <td>{{ c.industryName }}</td>
            <td>
              <span v-for="(d, j) in c.details" :key="j" class="chip"
                    :class="d.passed ? 'ok' : 'no'">
                {{ d.indicatorName }} {{ fmtNum(d.actualValue) }} {{ opText(d.operator) }} {{ fmtNum(d.value) }}{{ d.value2 != null ? '~' + fmtNum(d.value2) : '' }}
              </span>
            </td>
            <td><button class="secondary mini" @click="emit('select', { companyId: c.companyId, stockCode: c.stockCode, stockName: c.stockName, industryName: c.industryName })">查看画像 →</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.filterbar { gap: 14px; }
.cond { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; background: #f8f9fb; border: 1px solid #e8ecf2; border-radius: 8px; padding: 8px 10px; }
button.mini { padding: 4px 10px; font-size: 12px; }
button.danger { background: #c0392b; }
.chip { display: inline-block; margin: 2px 4px 2px 0; padding: 2px 8px; border-radius: 12px; font-size: 12px; background: #eef2f8; color: #445; white-space: nowrap; }
.chip.ok { background: #e6f4ea; color: #1e7e34; }
.chip.no { background: #fdecea; color: #c0392b; }
</style>
