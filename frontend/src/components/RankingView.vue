<script setup>
import { ref, watch, onMounted } from 'vue'
import { api, fmtNum, directionText, YEARS } from '../api'

const emit = defineEmits(['select'])

const industries = ref([])
const indicators = ref([])          // 指标元数据
const industryId = ref('')
const year = ref(2025)
const code = ref('roe')
const rows = ref([])
const loading = ref(false)
const err = ref('')

const metaMap = new Map()           // code -> meta

async function loadMeta() {
  try {
    const [is, inds] = await Promise.all([api.industries(), api.indicators()])
    industries.value = is
    indicators.value = inds
    inds.forEach(m => metaMap.set(m.code, m))
    syncMeta()
    if (!industryId.value && is.length) industryId.value = is[0].industryId
  } catch (e) { err.value = e.message }
}

async function load() {
  if (!industryId.value || !code.value) return
  loading.value = true
  err.value = ''
  try {
    const data = await api.ranking({ industryId: industryId.value, fiscalYear: year.value, indicatorCode: code.value })
    rows.value = [...data].sort((a, b) => (a.rank || 99) - (b.rank || 99))
  } catch (e) { err.value = e.message; rows.value = [] } finally { loading.value = false }
}

onMounted(async () => { await loadMeta(); load() })
watch([industryId, year, code], load)

const currentMeta = ref(null)
function syncMeta() { currentMeta.value = metaMap.get(code.value) || null }
watch(code, syncMeta)

const byDim = (dim) => indicators.value.filter(i => i.dimension === dim)
</script>

<template>
  <div>
    <div class="card">
      <div class="row">
        <h2 style="font-size:18px;color:#1f3b63">🏆 行业指标排行</h2>
      </div>
      <div class="row mt filterbar">
        <label class="muted">行业
          <select v-model="industryId">
            <option v-for="i in industries" :key="i.industryId" :value="i.industryId">
              {{ i.industryName }}({{ i.companyCount }}家)
            </option>
          </select>
        </label>
        <label class="muted">财年
          <select v-model.number="year">
            <option v-for="y in YEARS" :key="y" :value="y">{{ y }}</option>
          </select>
        </label>
        <label class="muted">指标
          <select v-model="code" style="min-width:220px">
            <optgroup v-for="dim in ['盈利能力','成长性','财务风险','盈利质量','每股指标','估值']" :key="dim" :label="dim">
              <option v-for="m in byDim(dim)" :key="m.code" :value="m.code">{{ m.name }}</option>
            </optgroup>
          </select>
        </label>
        <span v-if="currentMeta" class="muted" style="margin-left:auto">
          单位 {{ currentMeta.unit }} · {{ directionText(currentMeta.betterDirection) }} · 排名 1 = 最优
        </span>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
      <p v-if="loading" class="muted mt">加载中…</p>
    </div>

    <div class="card mt" v-if="rows.length">
      <table>
        <thead>
          <tr>
            <th style="width:70px">排名</th><th>股票代码</th><th>股票简称</th>
            <th class="num">{{ (metaMap.get(code) || {}).name || code }}</th>
            <th class="num">行业百分位</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.companyId">
            <td><span class="medal" v-if="r.rank === 1">🥇</span><span class="medal" v-else-if="r.rank === 2">🥈</span><span class="medal" v-else-if="r.rank === 3">🥉</span>{{ r.rank }}</td>
            <td>{{ r.stockCode }}</td>
            <td>{{ r.stockName }}</td>
            <td class="num">{{ fmtNum(r.value) }} <span class="muted">{{ (metaMap.get(code) || {}).unit }}</span></td>
            <td class="num">{{ fmtNum(r.percentile) }}</td>
            <td><button class="secondary mini" @click="emit('select', { companyId: r.companyId, stockCode: r.stockCode, stockName: r.stockName })">查看画像 →</button></td>
          </tr>
        </tbody>
      </table>
      <p class="muted mt">💡 点击「查看画像」跳转财务画像 · 行业对标页</p>
    </div>
    <div v-else-if="!loading" class="card mt muted">该行业 / 年度暂无此指标数据</div>
  </div>
</template>

<style scoped>
.filterbar { gap: 14px; }
button.mini { padding: 4px 10px; font-size: 12px; }
.medal { margin-right: 6px; }
</style>
