<script setup>
// 通用 ECharts 容器: 传入 option 即渲染; 自适应窗口; 卸载时释放
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '330px' }
})

const el = ref(null)
let chart = null

function onResize() { chart && chart.resize() }

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value)
  chart.setOption(props.option, true)
}

onMounted(() => {
  render()
  window.addEventListener('resize', onResize)
})

watch(() => props.option, () => nextTick(render), { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (chart) { chart.dispose(); chart = null }
})
</script>

<template>
  <div ref="el" :style="{ width: '100%', height }"></div>
</template>
