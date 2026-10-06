<script setup>
/** 统一空状态 / 错误态 */
defineProps({
  icon: { type: String, default: '📭' },
  title: { type: String, default: '暂无数据' },
  desc: { type: String, default: '' },
  actionText: { type: String, default: '' },
  tone: { type: String, default: 'mute' } // mute | error
})
defineEmits(['action'])
</script>

<template>
  <div class="empty">
    <div class="e-ico">{{ tone === 'error' ? '⚠️' : icon }}</div>
    <div class="e-title" :class="{ 'text-down': tone === 'error' }">{{ title }}</div>
    <div v-if="desc" class="e-desc">{{ desc }}</div>
    <button v-if="actionText" class="btn btn-ghost btn-sm mt-2" @click="$emit('action')">{{ actionText }}</button>
  </div>
</template>
