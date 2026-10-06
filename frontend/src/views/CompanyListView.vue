<script setup>
/** 公司查询: 关键字 + 行业筛选, 表格/卡片双视图, 分页 */
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { store, toast } from '../store'
import EmptyState from '../components/EmptyState.vue'
import SkeletonTable from '../components/SkeletonTable.vue'

defineOptions({ name: 'CompanyListView' })
const emit = defineEmits(['select', 'navigate'])

const keyword = ref('')
const industryId = ref('')
const page = ref(1)
const size = ref(12)
const list = ref([])
const total = ref(0)
const pages = ref(0)
const loading = ref(false)
const err = ref('')
const view = ref('table')   // table | card

const industryMap = computed(() => store.industryMap)

async function load() {
  loading.value = true
  err.value = ''
  try {
    const data = await api.companies({
      keyword: keyword.value.trim() || undefined,
      industryId: industryId.value || undefined,
      page: page.value,
      size: size.value
    })
    list.value = data.list || []
    total.value = data.total || 0
    pages.value = Math.max(1, Math.ceil(total.value / size.value))
    if (page.value > pages.value) { page.value = pages.value; return load() }
  } catch (e) {
    err.value = e.message
    list.value = []
    total.value = 0
    pages.value = 1
  } finally {
    loading.value = false
  }
}

function doSearch() { page.value = 1; load() }
function reset() { keyword.value = ''; industryId.value = ''; doSearch() }

function pick(c) {
  emit('select', c)
  toast(`已选择 ${c.stockName}`, 'ok', 1800)
}

/** 分页页码(最多 7 个, 两端省略) */
const pageItems = computed(() => {
  const p = page.value, n = pages.value
  if (n <= 7) return Array.from({ length: n }, (_, i) => i + 1)
  const set = new Set([1, n, p, p - 1, p + 1])
  if (p <= 3) [2, 3, 4].forEach(x => set.add(x))
  if (p >= n - 2) [n - 1, n - 2, n - 3].forEach(x => set.add(x))
  const arr = [...set].filter(x => x >= 1 && x <= n).sort((a, b) => a - b)
  const out = []
  arr.forEach((x, i) => {
    if (i && x - arr[i - 1] > 1) out.push('…')
    out.push(x)
  })
  return out
})

watch(size, doSearch)
onMounted(load)

const exchangeTag = (ex) => (ex === 'SH' ? '上海证券交易所' : ex === 'SZ' ? '深圳证券交易所' : ex)
</script>

<template>
  <div class="list-view">
    <!-- 检索区 -->
    <div class="card">
      <div class="card-hd">
        <div class="card-title"><span class="ico">🔍</span>样本公司检索</div>
        <span class="card-sub">共收录 {{ total }} 家 · 数据来源为公开财报接口</span>
        <div class="card-tools">
          <div class="segmented">
            <button :class="{ on: view === 'table' }" @click="view = 'table'">☰ 表格</button>
            <button :class="{ on: view === 'card' }" @click="view = 'card'">▦ 卡片</button>
          </div>
        </div>
      </div>

      <div class="filter-row card-bd">
        <div class="search-box grow">
          <span class="s-ico">🔎</span>
          <input
            v-model="keyword" type="search"
            placeholder="输入股票代码 / 简称 / 公司全称, 回车检索"
            @keyup.enter="doSearch"
          />
        </div>
        <select v-model="industryId" class="ind-select" @change="doSearch">
          <option value="">全部行业</option>
          <option v-for="i in store.industries" :key="i.industryId" :value="i.industryId">
            {{ i.industryName }}({{ i.companyCount }}家)
          </option>
        </select>
        <button class="btn" :disabled="loading" @click="doSearch">查询</button>
        <button class="btn btn-subtle" @click="reset">重置</button>
      </div>
    </div>

    <!-- 结果 -->
    <div class="card">
      <p v-if="err" class="alert"><span>⛔</span><span>{{ err }}</span>
        <button class="btn btn-ghost btn-xs" style="margin-left:auto" @click="load">重试</button>
      </p>

      <SkeletonTable v-if="loading" :rows="6" :cols="5" />

      <template v-else-if="!err">
        <EmptyState
          v-if="!list.length" icon="🔍" title="没有匹配的公司"
          desc="试试更换关键字, 或清空行业筛选条件后重新检索。"
          action-text="重置筛选条件" @action="reset"
        />

        <!-- 表格视图 -->
        <div v-else-if="view === 'table'" class="tbl-wrap">
          <table class="tbl">
            <thead>
              <tr>
                <th style="width:96px">股票代码</th>
                <th style="width:110px">股票简称</th>
                <th class="hide-sm">公司全称</th>
                <th style="width:210px">所属行业</th>
                <th class="center" style="width:120px">交易所</th>
                <th class="center" style="width:110px">上市日期</th>
                <th class="center" style="width:96px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in list" :key="c.companyId" class="clickable"
                :class="{ 'is-active': store.selectedCompany && store.selectedCompany.companyId === c.companyId }"
                @click="pick(c)"
              >
                <td class="mono">{{ c.stockCode }}</td>
                <td><b>{{ c.stockName }}</b></td>
                <td class="muted hide-sm">{{ c.fullName }}</td>
                <td><span class="tag mute">{{ c.industryName }}</span></td>
                <td class="center"><span class="tag">{{ exchangeTag(c.exchange) }}</span></td>
                <td class="center muted">{{ c.listDate }}</td>
                <td class="center">
                  <button class="btn btn-ghost btn-xs" @click.stop="pick(c)">查看画像 →</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 卡片视图 -->
        <div v-else class="card-grid">
          <button
            v-for="c in list" :key="c.companyId" class="co-card"
            :class="{ on: store.selectedCompany && store.selectedCompany.companyId === c.companyId }"
            @click="pick(c)"
          >
            <div class="cc-head">
              <span class="cc-name">{{ c.stockName }}</span>
              <span class="cc-code mono">{{ c.stockCode }}</span>
            </div>
            <div class="cc-full muted">{{ c.fullName }}</div>
            <div class="cc-foot">
              <span class="tag mute">{{ c.industryName }}</span>
              <span class="tag">{{ exchangeTag(c.exchange) }}</span>
            </div>
            <div class="cc-date muted">上市 {{ c.listDate }}</div>
          </button>
        </div>
      </template>

      <!-- 分页 -->
      <div v-if="!loading && total > 0" class="pager">
        <span class="muted">共 {{ total }} 条 · 第 {{ page }}/{{ pages }} 页</span>
        <div class="pager-ctrl">
          <select v-model.number="size" class="size-select">
            <option :value="12">12 / 页</option>
            <option :value="24">24 / 页</option>
            <option :value="48">48 / 页</option>
          </select>
          <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; load()">上一页</button>
          <template v-for="(p, i) in pageItems" :key="i">
            <span v-if="p === '…'" class="muted px">…</span>
            <button v-else class="page-btn" :class="{ on: p === page }" @click="page = p; load()">{{ p }}</button>
          </template>
          <button class="btn btn-ghost btn-sm" :disabled="page >= pages" @click="page++; load()">下一页</button>
        </div>
      </div>

      <div v-if="!loading && list.length" class="hint-row muted">
        💡 点击任意一行 / 卡片即可载入该公司, 系统会自动跳转到「财务画像 · 行业对标」
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-view { display: flex; flex-direction: column; gap: var(--sp-5); }

.filter-row { display: flex; gap: var(--sp-3); align-items: center; flex-wrap: wrap; }
.filter-row .search-box { flex: 1 1 260px; }
.ind-select { width: 300px; max-width: 100%; }

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(228px, 1fr)); gap: var(--sp-4); }
.co-card {
  display: flex; flex-direction: column; gap: 7px; text-align: left;
  padding: 14px 15px; font-family: inherit;
  background: var(--c-surface); border: 1px solid var(--c-border); border-radius: var(--r-lg);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.co-card:hover { border-color: var(--c-brand-300); box-shadow: var(--sh-2); transform: translateY(-2px); }
.co-card.on { border-color: var(--c-brand-500); background: var(--c-brand-50); }
.cc-head { display: flex; align-items: baseline; gap: 8px; }
.cc-name { font-size: 15px; font-weight: 600; color: var(--c-brand-800); }
.cc-code { font-size: 12px; color: var(--c-text-3); }
.cc-full { font-size: 12px; line-height: 1.5; min-height: 36px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cc-foot { display: flex; gap: 6px; flex-wrap: wrap; }
.cc-foot .tag { max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.cc-date { font-size: 11.5px; }

.pager { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); flex-wrap: wrap; margin-top: var(--sp-4); padding-top: var(--sp-4); border-top: 1px solid var(--c-border); }
.pager-ctrl { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.size-select { width: 92px; min-height: 30px; font-size: 12.5px; }
.page-btn {
  min-width: 30px; height: 30px; padding: 0 8px;
  font-family: inherit; font-size: 12.5px; color: var(--c-text-2);
  background: var(--c-surface); border: 1px solid var(--c-border-2); border-radius: var(--r-sm);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.page-btn:hover { color: var(--c-brand-500); border-color: var(--c-brand-300); background: var(--c-brand-50); }
.page-btn.on { color: #fff; background: var(--c-brand-600); border-color: var(--c-brand-600); }
.px { padding: 0 2px; }
.hint-row { margin-top: var(--sp-3); font-size: 12.5px; }
</style>
