<script setup>
/** KPI 指标卡: 用于概览页与画像页顶部的关键数字展示 */
import AppIcon from './AppIcon.vue'
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  unit: { type: String, default: '' },
  icon: { type: String, default: '' },
  hint: { type: String, default: '' },
  /** 变化描述, 如 "↑ 2.3% 高于行业中位数" */
  trend: { type: String, default: '' },
  trendTone: { type: String, default: 'mute' }, // ok | bad | warn | mute
  accent: { type: String, default: 'brand' }    // brand | up | down | warn | purple
})
</script>

<template>
  <div class="stat" :class="`accent-${accent}`">
    <div class="s-top">
      <span class="s-label">{{ label }}</span>
      <span v-if="icon" class="s-ico"><AppIcon :name="icon" :size="16" /></span>
    </div>
    <div class="s-value">
      <span class="kpi-value sm">{{ value }}</span>
      <span v-if="unit" class="kpi-unit">{{ unit }}</span>
    </div>
    <div class="s-foot">
      <span v-if="trend" class="tag" :class="trendTone">{{ trend }}</span>
      <span v-if="hint" class="muted">{{ hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat {
  position: relative;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-lg);
  padding: 14px 16px 13px;
  box-shadow: var(--sh-1);
  overflow: hidden;
  transition: box-shadow var(--dur) var(--ease), transform var(--dur) var(--ease);
}
.stat:hover { box-shadow: var(--sh-2); transform: translateY(-1px); }
.stat::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--c-brand-500); }
.accent-up::before { background: var(--c-up); }
.accent-down::before { background: var(--c-down); }
.accent-warn::before { background: var(--c-warn); }
.accent-purple::before { background: var(--c-purple); }

.s-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.s-label { font-size: 12.5px; color: var(--c-text-3); }
.s-ico { font-size: 15px; opacity: .55; }
.s-value { display: flex; align-items: baseline; margin: 4px 0 6px; }
.s-foot { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; min-height: 20px; }
</style>