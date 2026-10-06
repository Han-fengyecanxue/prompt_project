<script setup>
/**
 * 通用侧滑抽屉
 * - Teleport 到 body, 避免被父容器 overflow/stacking context 限制
 * - 支持 Esc 关闭、遮罩点击关闭、打开时锁定 body 滚动
 */
import { watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  width: { type: String, default: '560px' }
})
const emit = defineEmits(['update:modelValue'])

function close() { emit('update:modelValue', false) }

function onKeydown(e) { if (e.key === 'Escape' && props.modelValue) close() }

watch(() => props.modelValue, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onMounted(() => document.addEventListener('keydown', onKeydown))

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <transition name="drawer">
      <div v-if="modelValue" class="drawer-root no-print">
        <div class="drawer-mask" @click="close"></div>
        <aside class="drawer" :style="{ width }" role="dialog" aria-modal="true">
          <header class="drawer-hd">
            <div class="dh-text">
              <h3>{{ title }}</h3>
              <span v-if="subtitle" class="muted">{{ subtitle }}</span>
            </div>
            <div class="dh-tools">
              <slot name="tools"></slot>
              <button class="icon-btn" title="关闭 (Esc)" @click="close">✕</button>
            </div>
          </header>
          <div class="drawer-bd">
            <slot></slot>
          </div>
          <footer v-if="$slots.footer" class="drawer-ft">
            <slot name="footer"></slot>
          </footer>
        </aside>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.drawer-root { position: fixed; inset: 0; z-index: 250; }
.drawer-mask { position: absolute; inset: 0; background: rgba(16, 35, 61, .34); backdrop-filter: blur(1px); }
.drawer {
  position: absolute; top: 0; right: 0; bottom: 0; max-width: 94vw;
  display: flex; flex-direction: column;
  background: var(--c-surface); box-shadow: -8px 0 32px rgba(16, 35, 61, .18);
}
.drawer-hd {
  display: flex; align-items: flex-start; gap: var(--sp-3);
  padding: 14px 16px; border-bottom: 1px solid var(--c-border); flex: none;
}
.dh-text { min-width: 0; }
.dh-text h3 { font-size: 15px; color: var(--c-brand-800); }
.dh-tools { margin-left: auto; display: flex; align-items: center; gap: 4px; flex: none; }
.drawer-bd { flex: 1; overflow-y: auto; padding: 16px; }
.drawer-ft { flex: none; padding: 12px 16px; border-top: 1px solid var(--c-border); background: var(--c-surface-2); display: flex; gap: 8px; flex-wrap: wrap; }

.drawer-enter-active, .drawer-leave-active { transition: opacity .2s var(--ease); }
.drawer-enter-active .drawer, .drawer-leave-active .drawer { transition: transform .22s var(--ease); }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(100%); }
</style>
