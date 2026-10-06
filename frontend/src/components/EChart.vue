<script setup>
/**
 * 通用 ECharts 容器
 * - 自动应用 'fin' 主题
 * - 使用 ResizeObserver 跟随容器尺寸变化(优于监听 window.resize: 侧边栏折叠/栅格变化也能自适应)
 * - 支持 loading 骨架与空数据占位
 * - 卸载时 dispose, 避免内存泄漏
 */
import { ref, onMounted, onBeforeUnmount, watch, nextTick, shallowRef } from 'vue'
import echarts, { emptyOption } from '../utils/charts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
  loading: { type: Boolean, default: false },
  empty: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  /** 是否显示"下载图片"工具按钮 */
  savable: { type: Boolean, default: true },
  filename: { type: String, default: 'chart' }
})

const el = ref(null)
const chart = shallowRef(null)
let ro = null
let raf = 0

function render() {
  if (!el.value) return
  if (!chart.value) {
    chart.value = echarts.init(el.value, 'fin', { renderer: 'canvas' })
  }
  const opt = props.empty ? emptyOption(props.emptyText) : props.option
  chart.value.setOption(opt, true)
}

function resize() {
  cancelAnimationFrame(raf)
  raf = requestAnimationFrame(() => chart.value && chart.value.resize({ animation: { duration: 200 } }))
}

onMounted(async () => {
  await nextTick()
  // 极端情况下(父级在同一 tick 内切换 v-if / 组件被立即移除), nextTick 后元素可能已销毁,
  // 此时 observe 会抛 "parameter 1 is not of type 'Element'", 直接跳过即可。
  if (!el.value) return
  render()
  if (typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(resize)
    ro.observe(el.value)
  } else {
    window.addEventListener('resize', resize)
  }
})

watch(() => [props.option, props.empty], () => nextTick(render), { deep: true })
watch(() => props.loading, (v) => {
  if (!chart.value) return
  if (v) chart.value.showLoading('default', {
    text: '加载中', color: '#2f6fd0', textColor: '#8a97a8',
    maskColor: 'rgba(255,255,255,.75)', fontSize: 12, spinnerRadius: 9, lineWidth: 2
  })
  else chart.value.hideLoading()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  if (ro) { ro.disconnect(); ro = null } else { window.removeEventListener('resize', resize) }
  if (chart.value) { chart.value.dispose(); chart.value = null }
})

function saveImage() {
  if (!chart.value) return
  const url = chart.value.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.filename}.png`
  a.click()
}
defineExpose({ resize, saveImage, getInstance: () => chart.value })
</script>

<template>
  <div class="chart-shell">
    <div ref="el" class="chart-canvas" :style="{ height }"></div>
    <div v-if="savable && !empty && !loading" class="chart-tools no-print">
      <button class="icon-btn" title="下载 PNG 图片" @click="saveImage">⤓</button>
    </div>
  </div>
</template>

<style scoped>
.chart-shell { position: relative; width: 100%; }
.chart-canvas { width: 100%; }
.chart-tools {
  position: absolute; top: 0; right: 0; display: flex; gap: 2px;
  opacity: 0; transition: opacity var(--dur) var(--ease);
}
.chart-shell:hover .chart-tools { opacity: 1; }
.chart-tools .icon-btn { width: 28px; height: 28px; font-size: 14px; background: rgba(255,255,255,.9); border: 1px solid var(--c-border); }
</style>
