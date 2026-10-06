<script setup>
/** 表格骨架屏: rows 行 × cols 列 */
defineProps({
  rows: { type: Number, default: 5 },
  cols: { type: Number, default: 5 }
})
</script>

<template>
  <div class="sk-tbl">
    <div v-for="r in rows" :key="r" class="sk-row">
      <div v-for="c in cols" :key="c" class="sk sk-line" :style="{ width: c === 1 ? '70%' : `${45 + ((r * c) % 40)}%` }"></div>
    </div>
  </div>
</template>

<style scoped>
.sk-tbl { padding: 8px 0; }
.sk-row { display: grid; grid-template-columns: repeat(v-bind(cols), 1fr); gap: 20px; padding: 9px 12px; border-bottom: 1px solid var(--c-border); }
.sk-row .sk-line { margin: 0; }
</style>
