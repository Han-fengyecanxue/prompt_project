<script setup>
/** 全局通知容器: 固定右上角, 自动消失 */
import { store, dismissToast } from '../store'

const ICONS = { info: 'ℹ️', ok: '✅', warn: '⚠️', error: '⛔' }
</script>

<template>
  <div class="toast-host no-print">
    <transition-group name="toast">
      <div v-for="t in store.toasts" :key="t.id" class="toast" :class="t.type" @click="dismissToast(t.id)">
        <span class="t-ico">{{ ICONS[t.type] || ICONS.info }}</span>
        <span class="t-msg">{{ t.message }}</span>
        <button class="t-close" aria-label="关闭" @click.stop="dismissToast(t.id)">×</button>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed; top: 16px; right: 16px; z-index: 200;
  display: flex; flex-direction: column; gap: 8px; max-width: 380px;
}
.toast {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 10px 12px; font-size: 13px; line-height: 1.5;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-left: 3px solid var(--c-brand-500);
  border-radius: var(--r-md); box-shadow: var(--sh-3); cursor: pointer;
}
.toast.ok { border-left-color: var(--c-up); }
.toast.warn { border-left-color: var(--c-warn); }
.toast.error { border-left-color: var(--c-down); }
.t-ico { flex: none; font-size: 14px; }
.t-msg { flex: 1; color: var(--c-text); word-break: break-word; }
.t-close { flex: none; border: none; background: none; font-size: 16px; line-height: 1; color: var(--c-text-3); cursor: pointer; padding: 0 2px; }
.t-close:hover { color: var(--c-text); }

.toast-enter-active, .toast-leave-active { transition: all .22s var(--ease); }
.toast-enter-from { opacity: 0; transform: translateX(24px); }
.toast-leave-to { opacity: 0; transform: translateX(24px); }
</style>
