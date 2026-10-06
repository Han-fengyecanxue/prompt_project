<script setup>
/**
 * 公司选择器(顶栏全局组件)
 * 支持: 关键字远程检索(带防抖) / 键盘上下选择 + 回车确认 / 点击外部关闭
 */
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { api } from '../api'
import { store, selectCompany } from '../store'

const open = ref(false)
const keyword = ref('')
const list = ref([])
const loading = ref(false)
const err = ref('')
const activeIdx = ref(-1)
const rootEl = ref(null)
let timer = 0
let reqSeq = 0

const current = computed(() => store.selectedCompany)

async function search() {
  const seq = ++reqSeq
  loading.value = true
  err.value = ''
  try {
    const data = await api.companies({ keyword: keyword.value.trim() || undefined, page: 1, size: 30 })
    if (seq !== reqSeq) return
    list.value = data.list || []
    activeIdx.value = list.value.length ? 0 : -1
  } catch (e) {
    if (seq !== reqSeq) return
    err.value = e.message
    list.value = []
  } finally {
    if (seq === reqSeq) loading.value = false
  }
}

watch(keyword, () => {
  clearTimeout(timer)
  timer = setTimeout(search, 220)
})

function toggle() {
  open.value = !open.value
  if (open.value) {
    nextTick(() => { if (!list.value.length) search() })
  }
}

function choose(c) {
  selectCompany(c)
  open.value = false
  keyword.value = ''
}

function onKeydown(e) {
  if (!open.value) { if (e.key === 'Enter') toggle(); return }
  if (e.key === 'ArrowDown') { e.preventDefault(); activeIdx.value = Math.min(activeIdx.value + 1, list.value.length - 1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); activeIdx.value = Math.max(activeIdx.value - 1, 0) }
  else if (e.key === 'Enter') { e.preventDefault(); if (list.value[activeIdx.value]) choose(list.value[activeIdx.value]) }
  else if (e.key === 'Escape') { open.value = false }
}

function onClickOutside(e) {
  if (rootEl.value && !rootEl.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('click', onClickOutside, true))
onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside, true)
  clearTimeout(timer)
})
</script>

<template>
  <div ref="rootEl" class="picker" @keydown="onKeydown">
    <button class="picker-btn" :class="{ on: open }" @click="toggle">
      <span class="p-ico">🏢</span>
      <template v-if="current">
        <span class="p-name">{{ current.stockName }}</span>
        <span class="p-code mono">{{ current.stockCode }}</span>
      </template>
      <span v-else class="p-ph">选择公司…</span>
      <span class="p-caret">▾</span>
    </button>

    <transition name="fade">
      <div v-if="open" class="picker-pop">
        <div class="pp-head">
          <div class="search-box">
            <span class="s-ico">🔎</span>
            <input v-model="keyword" type="search" placeholder="代码 / 简称 / 全称" autofocus />
          </div>
        </div>
        <div class="pp-body">
          <p v-if="loading" class="muted pp-tip">加载中…</p>
          <p v-else-if="err" class="alert pp-tip">{{ err }}</p>
          <p v-else-if="!list.length" class="muted pp-tip">未找到匹配的公司</p>
          <ul v-else class="pp-list">
            <li
              v-for="(c, i) in list" :key="c.companyId"
              :class="{ on: i === activeIdx, active: current && current.companyId === c.companyId }"
              @mouseenter="activeIdx = i"
              @click="choose(c)"
            >
              <span class="pl-code mono">{{ c.stockCode }}</span>
              <span class="pl-name">{{ c.stockName }}</span>
              <span class="pl-ind muted">{{ c.industryName }}</span>
            </li>
          </ul>
        </div>
        <div class="pp-foot muted">↑↓ 选择 · Enter 确认 · Esc 关闭</div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.picker { position: relative; }
.picker-btn {
  display: flex; align-items: center; gap: 7px;
  height: 36px; padding: 0 12px; min-width: 208px;
  font-family: inherit; font-size: 13px; color: var(--c-text);
  background: var(--c-surface); border: 1px solid var(--c-border-2); border-radius: var(--r-md);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.picker-btn:hover, .picker-btn.on { border-color: var(--c-brand-400); box-shadow: 0 0 0 3px rgba(74,137,224,.14); }
.p-ico { font-size: 14px; opacity: .7; }
.p-name { font-weight: 500; }
.p-code { font-size: 11.5px; color: var(--c-text-3); }
.p-ph { color: #a9b5c4; }
.p-caret { margin-left: auto; font-size: 10px; color: var(--c-text-3); }

.picker-pop {
  position: absolute; top: calc(100% + 6px); right: 0; z-index: 90;
  width: 380px; max-width: min(380px, 88vw);
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-lg); box-shadow: var(--sh-3); overflow: hidden;
}
.pp-head { padding: 10px; border-bottom: 1px solid var(--c-border); background: var(--c-surface-2); }
.pp-body { max-height: 320px; overflow-y: auto; }
.pp-tip { padding: 16px; text-align: center; }
.pp-list { list-style: none; margin: 0; padding: 4px; }
.pp-list li {
  display: flex; align-items: center; gap: 9px;
  padding: 8px 10px; border-radius: var(--r-sm); cursor: pointer;
}
.pp-list li.on { background: var(--c-brand-50); }
.pp-list li.active .pl-name { font-weight: 600; color: var(--c-brand-600); }
.pl-code { font-size: 12px; color: var(--c-text-3); width: 54px; flex: none; }
.pl-name { font-size: 13.5px; }
.pl-ind { margin-left: auto; font-size: 11.5px; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pp-foot { padding: 6px 12px; border-top: 1px solid var(--c-border); background: var(--c-surface-2); font-size: 11.5px; }

@media (max-width: 860px) { .picker-btn { min-width: 0; } .p-name, .p-code { display: none; } }
</style>
