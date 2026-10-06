<script setup>
/** 顶栏: 页面标题 / 全局财年 / 公司选择 / 后端状态 / 显示密度 */
import { computed } from 'vue'
import CompanyPicker from './CompanyPicker.vue'
import { store, setYear, checkHealth, toggleDensity, toggleSidebar } from '../store'
import { YEARS } from '../api'
import { navMeta } from '../utils/nav'

const props = defineProps({ active: { type: String, required: true } })
const meta = computed(() => navMeta(props.active))

const healthText = computed(() => ({
  ok: '服务正常', degraded: '数据库异常', down: '后端未连接', unknown: '检测中…'
}[store.healthState]))

const healthTip = computed(() => {
  const h = store.health
  if (!h) return '点击重新检测后端服务(http://localhost:8091)'
  return [
    `应用: ${h.app}`,
    `服务: ${h.status}`,
    `数据库: ${h.database}`,
    `AI 模式: ${h.aiProvider}`,
    `时间: ${h.time}`
  ].join(' / ')
})
</script>

<template>
  <header class="topbar no-print">
    <button class="icon-btn menu-btn" title="展开/收起导航" @click="toggleSidebar">☰</button>

    <div class="tb-title">
      <h1>{{ meta.label }}</h1>
      <span class="tb-hint hide-sm">{{ meta.hint }}</span>
    </div>

    <div class="tb-tools">
      <label class="year-box" title="全局财年: 影响画像 / AI 解读 / 排行 / 筛选">
        <span class="yb-label hide-sm">财年</span>
        <select :value="store.year" @change="setYear($event.target.value)">
          <option v-for="y in YEARS" :key="y" :value="y">{{ y }}</option>
        </select>
      </label>

      <CompanyPicker />

      <button class="health" :class="store.healthState" :title="healthTip" @click="checkHealth">
        <span class="dot" :class="[store.healthState === 'ok' ? 'ok' : store.healthState === 'down' ? 'bad' : 'warn', { pulse: store.healthChecking }]"></span>
        <span class="h-text hide-sm">{{ healthText }}</span>
        <span class="h-ai hide-sm" v-if="store.health && store.health.aiProvider">AI:{{ store.health.aiProvider }}</span>
      </button>

      <button class="icon-btn" :title="store.density === 'compact' ? '切换到宽松排版' : '切换到紧凑排版'" @click="toggleDensity">
        {{ store.density === 'compact' ? '▤' : '▦' }}
      </button>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  display: flex; align-items: center; gap: var(--sp-3);
  height: var(--topbar-h); flex: none;
  padding: 0 var(--sp-6);
  background: rgba(255,255,255,.88);
  backdrop-filter: saturate(180%) blur(8px);
  border-bottom: 1px solid var(--c-border);
  position: sticky; top: 0; z-index: 60;
}
.menu-btn { display: none; }
@media (max-width: 860px) { .menu-btn { display: inline-flex; } }

.tb-title { display: flex; align-items: baseline; gap: 10px; min-width: 0; }
.tb-title h1 { font-size: 16.5px; color: var(--c-brand-800); white-space: nowrap; }
.tb-hint { font-size: 12px; color: var(--c-text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.tb-tools { margin-left: auto; display: flex; align-items: center; gap: var(--sp-3); flex-wrap: nowrap; }

.year-box { display: inline-flex; align-items: center; gap: 6px; }
.yb-label { font-size: 12.5px; color: var(--c-text-2); }
.year-box select { width: 84px; min-height: 36px; }

.health {
  display: inline-flex; align-items: center; gap: 7px;
  height: 36px; padding: 0 12px;
  font-family: inherit; font-size: 12.5px; color: var(--c-text-2);
  background: var(--c-surface); border: 1px solid var(--c-border-2); border-radius: var(--r-md);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.health:hover { border-color: var(--c-brand-300); background: var(--c-brand-50); }
.health.down { color: var(--c-down); border-color: #f0c4c7; background: var(--c-down-bg); }
.h-ai { font-size: 11px; color: var(--c-text-3); padding-left: 6px; border-left: 1px solid var(--c-border); }

@media (max-width: 1180px) {
  .tb-hint, .h-ai { display: none; }
}
</style>
