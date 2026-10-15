<script setup>
/** 左侧导航栏 */
import { store, toggleSidebar, companyCount } from '../store'
import { NAV } from '../utils/nav'
import AppIcon from './AppIcon.vue'

defineProps({ active: { type: String, required: true } })
const emit = defineEmits(['navigate'])
</script>

<template>
  <aside class="sidebar no-print" :class="{ collapsed: store.sidebarCollapsed }">
    <div class="brand" @click="emit('navigate', 'dashboard')">
      <div class="logo">
        <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">
          <rect x="1" y="1" width="30" height="30" rx="8" fill="url(#lg)" />
          <rect x="8" y="17" width="3.6" height="7" rx="1.2" fill="#fff" opacity=".92" />
          <rect x="14.2" y="12" width="3.6" height="12" rx="1.2" fill="#fff" opacity=".92" />
          <rect x="20.4" y="8" width="3.6" height="16" rx="1.2" fill="#fff" />
          <defs>
            <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#4a89e0" />
              <stop offset="100%" stop-color="#17406f" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <div v-show="!store.sidebarCollapsed" class="brand-text">
        <div class="brand-name">财报智读</div>
        <div class="brand-sub">Prompt 工程 · 行业对标</div>
      </div>
    </div>

    <nav class="nav">
      <button
        v-for="item in NAV" :key="item.key"
        class="nav-item" :class="{ on: active === item.key }"
        :title="store.sidebarCollapsed ? item.label : ''"
        @click="emit('navigate', item.key)"
      >
        <span class="n-ico"><AppIcon :name="item.icon" :size="17" /></span>
        <span v-show="!store.sidebarCollapsed" class="n-text">
          <span class="n-label">{{ item.label }}</span>
          <span class="n-desc">{{ item.desc }}</span>
        </span>
        <span v-if="active === item.key" class="n-bar"></span>
      </button>
    </nav>

    <div class="side-foot">
      <div v-show="!store.sidebarCollapsed" class="foot-info">
        <div class="foot-row"><span class="dot ok"></span>数据源 东方财富 / 新浪</div>
        <div class="foot-row">样本 {{ companyCount }} 家 · 2021–2025 年报</div>
        <div class="foot-row dim2">v1.0</div>
      </div>
      <button class="icon-btn collapse-btn" :title="store.sidebarCollapsed ? '展开导航' : '收起导航'" @click="toggleSidebar">
        {{ store.sidebarCollapsed ? '»' : '«' }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  flex: none;
  display: flex; flex-direction: column;
  background: linear-gradient(180deg, #14304f 0%, #0d2340 100%);
  color: #cddcec;
  transition: width .2s var(--ease);
  overflow: hidden;
}
.sidebar.collapsed { width: var(--sidebar-w-collapsed); }

/* 品牌区 */
.brand { display: flex; align-items: center; gap: 10px; padding: 16px 14px 14px; cursor: pointer; user-select: none; }
.logo { flex: none; display: flex; }
.brand-text { min-width: 0; }
.brand-name { font-size: 15px; font-weight: 700; color: #fff; letter-spacing: .5px; }
.brand-sub { font-size: 11px; color: #7f9dc0; white-space: nowrap; }

/* 导航 */
.nav { flex: 1; padding: 8px 10px; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 11px;
  width: 100%; padding: 9px 10px;
  font-family: inherit; text-align: left;
  color: #a9c1dc; background: transparent;
  border: none; border-radius: var(--r-md); cursor: pointer;
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}
.nav-item:hover { background: rgba(255,255,255,.07); color: #fff; }
.nav-item.on { background: rgba(74,137,224,.22); color: #fff; }
.n-ico { flex: none; font-size: 16px; width: 20px; text-align: center; }
.n-text { display: flex; flex-direction: column; min-width: 0; }
.n-label { font-size: 13.5px; font-weight: 500; }
.n-desc { font-size: 11px; color: #7f9dc0; white-space: nowrap; }
.nav-item.on .n-desc { color: #a9c8ec; }
.n-bar { position: absolute; right: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 18px; border-radius: 3px 0 0 3px; background: #6fa8ff; }

/* 底部 */
.side-foot { padding: 10px 12px 12px; border-top: 1px solid rgba(255,255,255,.08); }
.foot-info { display: flex; flex-direction: column; gap: 5px; margin-bottom: 8px; }
.foot-row { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #8fabc9; white-space: nowrap; }
.foot-row.dim2 { color: #6d88a8; }
.collapse-btn { color: #8fabc9; width: 100%; }
.collapse-btn:hover { background: rgba(255,255,255,.08); color: #fff; }

@media (max-width: 860px) {
  .sidebar { position: fixed; left: 0; top: 0; bottom: 0; z-index: 120; box-shadow: var(--sh-3); }
}
</style>