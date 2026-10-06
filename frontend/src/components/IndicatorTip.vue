<script setup>
/**
 * 指标释义气泡
 * 点击指标名称弹出该指标的口径说明(名称/维度/单位/方向/计算公式)。
 * - 内容来自后端 /api/finance/indicators 的元数据 + 与 docs/技术文档.md「指标口径」表一致的公式文案
 * - 使用 Teleport 渲染到 body: 表格容器是 overflow:auto, 内联定位的气泡会被裁掉
 */
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { store } from '../store'
import { directionText } from '../utils/format'

const props = defineProps({
  code: { type: String, required: true },
  /** 不传则用元数据里的名称 */
  name: { type: String, default: '' },
  /** 紧凑模式: 用于表格内 */
  dense: { type: Boolean, default: false }
})

/**
 * 指标口径(须与 backend/docs/技术文档.md 的「指标口径」表保持一致;
 * 后端调整计算口径时, 这里与文档需同步更新)
 */
const FORMULA = {
  roe: '归母净利润 / 平均归属于母公司股东的权益 × 100%',
  gross_margin: '(营业收入 − 营业成本) / 营业收入 × 100%',
  net_margin_parent: '归母净利润 / 营业收入 × 100%',
  revenue_growth: '(本期营业收入 − 上期营业收入) / |上期营业收入| × 100%',
  profit_growth: '(本期归母净利润 − 上期) / |上期归母净利润| × 100%',
  asset_liability_ratio: '总负债 / 总资产 × 100%',
  current_ratio: '流动资产 / 流动负债',
  quick_ratio: '(流动资产 − 存货) / 流动负债',
  cashflow_quality: '经营活动现金流量净额 / 净利润',
  eps: '归母净利润 / 股本',
  pe: '总市值 / 归母净利润',
  pb: '总市值 / 归属于母公司股东的权益'
}

const open = ref(false)
const anchorEl = ref(null)
const popEl = ref(null)
const pos = ref({ top: 0, left: 0 })

const meta = computed(() => store.indicatorMap.get(props.code) || null)
const title = computed(() => props.name || (meta.value && meta.value.name) || props.code)

async function place() {
  await nextTick()
  if (!anchorEl.value) return
  const r = anchorEl.value.getBoundingClientRect()
  const W = 268
  const left = Math.min(Math.max(8, r.left), Math.max(8, window.innerWidth - W - 8))
  const below = r.bottom + 8
  // 视口下方空间不足时向上弹
  const top = below + 180 > window.innerHeight ? Math.max(8, r.top - 8 - 168) : below
  pos.value = { top, left }
}

function toggle() {
  open.value = !open.value
  if (open.value) place()
}

function onDocPointerDown(e) {
  if (!open.value) return
  if (anchorEl.value && anchorEl.value.contains(e.target)) return
  if (popEl.value && popEl.value.contains(e.target)) return
  open.value = false
}
function onKeydown(e) { if (e.key === 'Escape') open.value = false }
const onReflow = () => { if (open.value) place() }

onMounted(() => {
  document.addEventListener('pointerdown', onDocPointerDown, true)
  document.addEventListener('keydown', onKeydown)
  window.addEventListener('scroll', onReflow, true)
  window.addEventListener('resize', onReflow)
})
onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocPointerDown, true)
  document.removeEventListener('keydown', onKeydown)
  window.removeEventListener('scroll', onReflow, true)
  window.removeEventListener('resize', onReflow)
})
</script>

<template>
  <span ref="anchorEl" class="ind-tip" :class="{ dense }">
    <button type="button" class="ind-tip-btn" :aria-expanded="open" @click.stop="toggle">
      <span class="it-text">{{ title }}</span>
      <span class="it-mark" aria-hidden="true">?</span>
    </button>

    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="open" ref="popEl" class="ind-tip-pop no-print" role="dialog"
          :style="{ top: `${pos.top}px`, left: `${pos.left}px` }" @click.stop
        >
          <div class="pop-hd">
            <b>{{ title }}</b>
            <span class="muted mono">{{ code }}</span>
          </div>
          <dl class="pop-list">
            <div><dt>所属维度</dt><dd>{{ meta ? meta.dimension : '—' }}</dd></div>
            <div><dt>计量单位</dt><dd>{{ meta ? meta.unit : '—' }}</dd></div>
            <div>
              <dt>指标方向</dt>
              <dd>
                <span class="tag" :class="meta && meta.betterDirection === 'higher_better' ? 'ok' : 'warn'">
                  {{ meta && meta.betterDirection === 'higher_better' ? '↑' : '↓' }}
                  {{ meta ? directionText(meta.betterDirection) : '—' }}
                </span>
              </dd>
            </div>
            <div class="wide"><dt>计算口径</dt><dd class="mono">{{ FORMULA[code] || '见技术文档「指标口径」' }}</dd></div>
          </dl>
          <p v-if="meta" class="pop-foot muted">取值与行业对标均由后端计算引擎产出, 口径固定可复现。</p>
        </div>
      </transition>
    </Teleport>
  </span>
</template>

<style scoped>
.ind-tip { display: inline-flex; }
.ind-tip-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 0; font-family: inherit; font-size: inherit; color: inherit;
  background: none; border: none; cursor: help; text-align: left;
}
.it-text { border-bottom: 1px dashed var(--c-border-2); }
.ind-tip-btn:hover .it-text { color: var(--c-brand-600); border-bottom-color: var(--c-brand-300); }
.it-mark {
  display: inline-grid; place-items: center; flex: none;
  width: 13px; height: 13px; font-size: 9px; font-weight: 700;
  color: var(--c-text-3); background: var(--c-surface-3); border-radius: 50%;
}
.ind-tip-btn:hover .it-mark { color: #fff; background: var(--c-brand-400); }
.dense .it-mark { width: 12px; height: 12px; font-size: 8px; }
</style>

<style>
/* 气泡被 Teleport 到 body, 不能用 scoped */
.ind-tip-pop {
  position: fixed; z-index: 300; width: 268px;
  padding: 11px 13px; font-size: 12.5px; line-height: 1.6;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-md); box-shadow: var(--sh-3); color: var(--c-text);
}
.ind-tip-pop .pop-hd { display: flex; align-items: baseline; gap: 7px; padding-bottom: 7px; margin-bottom: 7px; border-bottom: 1px solid var(--c-border); }
.ind-tip-pop .pop-hd b { font-size: 13px; color: var(--c-brand-800); }
.ind-tip-pop .pop-list { margin: 0; display: flex; flex-wrap: wrap; gap: 6px 12px; }
.ind-tip-pop .pop-list > div { display: flex; align-items: baseline; gap: 6px; min-width: 0; }
.ind-tip-pop .pop-list > div.wide { flex-basis: 100%; flex-direction: column; gap: 2px; align-items: stretch; }
.ind-tip-pop dt { color: var(--c-text-3); font-size: 11.5px; white-space: nowrap; }
.ind-tip-pop dd { margin: 0; }
.ind-tip-pop dd.mono { font-size: 11.5px; background: var(--c-surface-2); padding: 4px 7px; border-radius: var(--r-sm); }
.ind-tip-pop .pop-foot { margin-top: 8px; padding-top: 7px; border-top: 1px dashed var(--c-border); font-size: 11px; }
</style>
