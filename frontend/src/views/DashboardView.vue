<script setup>
/**
 * 系统概览
 * 展示"项目定位 + 数据规模 + 指标体系 + 技术流程 + 运行状态"
 */
import { computed } from 'vue'
import StatCard from '../components/StatCard.vue'
import EChart from '../components/EChart.vue'
import EmptyState from '../components/EmptyState.vue'
import AppIcon from '../components/AppIcon.vue'
import { store, companyCount, indicatorsByDim, selectCompany, checkHealth } from '../store'
import { YEARS, LATEST_YEAR } from '../api'
import { categoryAxis, valueAxis, tooltip, PALETTE } from '../utils/charts'
import { directionText } from '../utils/format'

const emit = defineEmits(['navigate'])

const industryCount = computed(() => store.industries.length)
const indicatorCount = computed(() => store.indicators.length)

const industryOption = computed(() => {
  const data = store.industries.map(i => ({ name: i.industryName, value: i.companyCount }))
  return {
    tooltip: tooltip({ trigger: 'item', formatter: p => `${p.name}<br/>样本公司: <b>${p.value}</b> 家 (${p.percent}%)` }),
    series: [{
      type: 'pie',
      // 半径与标签宽度经过约束, 保证在 1366/1440 等窄屏下行业名称不会被画布裁掉
      radius: ['42%', '62%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#fff', borderWidth: 3 },
      label: {
        show: true,
        formatter: '{b|{b}}\n{c|{c} 家}',
        rich: {
          b: { fontSize: 11.5, color: '#52637a', lineHeight: 17, width: 126, align: 'center', overflow: 'break' },
          c: { fontSize: 13, color: '#12305a', fontWeight: 600, lineHeight: 18 }
        }
      },
      labelLine: { length: 8, length2: 8 },
      data
    }]
  }
})

const dimensionOption = computed(() => {
  const groups = indicatorsByDim.value
  return {
    tooltip: tooltip({ trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name}<br/>指标数量: <b>${p[0].value}</b> 项` }),
    grid: { left: 8, right: 40, top: 16, bottom: 8, containLabel: true },
    xAxis: valueAxis({ min: 0, minInterval: 1, splitLine: { show: false }, axisLine: { show: false } }),
    yAxis: categoryAxis(groups.map(g => g.dim), { inverse: true, axisLabel: { fontSize: 11.5, color: '#52637a' } }),
    series: [{
      type: 'bar',
      barWidth: 15,
      itemStyle: { borderRadius: [0, 6, 6, 0], color: (p) => PALETTE[p.dataIndex % PALETTE.length] },
      label: { show: true, position: 'right', fontSize: 11.5, color: '#52637a', formatter: '{c} 项' },
      data: groups.map(g => g.list.length)
    }]
  }
})

const healthRows = computed(() => {
  const h = store.health
  if (!h) return []
  return [
    { k: '后端服务', v: h.status === 'UP' ? '运行中' : h.status, ok: h.status === 'UP' },
    { k: '数据库连接', v: h.database === 'UP' ? '正常' : '异常', ok: h.database === 'UP' },
    { k: 'AI 供应商', v: h.aiProvider || '—', ok: true },
    { k: '服务时间', v: h.time || '—', ok: true }
  ]
})

const FLOW = [
  { n: '01', t: '数据采集', d: '东方财富 / 新浪公开接口抓取 2021–2025 年报原始科目', i: 'database' },
  { n: '02', t: '指标计算', d: '后端计算引擎由原始科目推导 12 项标准化财务指标', i: 'calculator' },
  { n: '03', t: '行业对标', d: '按 行业 × 年度 × 指标 统计均值/中位数/P25/P75 与百分位排名', i: 'rank' },
  { n: '04', t: 'Prompt 生成', d: '三层 Prompt(角色设定/数据注入/输出约束)驱动大模型撰写解读', i: 'ai' },
  { n: '05', t: '数值溯源', d: '校验报告数字能否在系统计算数据中找到出处, 抑制幻觉', i: 'search' }
]

/** 快捷入口: 挑一家代表公司直接体验完整链路 */
const demoCompany = { companyId: 17, stockCode: '600519', stockName: '贵州茅台', industryId: 3, industryName: '酒、饮料和精制茶制造业' }
function tryDemo() {
  selectCompany(demoCompany)
  emit('navigate', 'profile')
}
</script>

<template>
  <div class="dash">
    <!-- 项目定位 -->
    <section class="hero">
      <div class="hero-main">
        <div class="hero-badges">
          <span class="hb">省级大学生创新创业训练计划</span>
          <span class="hb hb-alt">Prompt 工程</span>
          <span class="hb hb-alt">双层解耦架构</span>
        </div>
        <h2>上市公司财报解读与行业对标系统</h2>
        <p class="hero-desc">
          底层由系统<strong>精确计算</strong>财务指标与行业分位(可溯源、可验证), 上层通过
          <strong>角色设定 + 数据注入 + 输出约束</strong> 三层 Prompt 驱动大模型生成自然语言解读,
          并校验报告中的每个数字是否来自系统数据, 从工程上抑制大模型幻觉。
        </p>
        <div class="hero-actions">
          <button class="btn" @click="emit('navigate', 'list')"><AppIcon name="search" :size="15" /> 开始公司查询</button>
          <button class="btn btn-ghost" @click="tryDemo">⚡ 体验完整链路(贵州茅台)</button>
        </div>
      </div>
      <div class="hero-side">
        <div class="hs-item"><span class="hs-k">技术栈</span><span class="hs-v">Spring Boot 3.4 · MyBatis · MySQL · Vue 3 · ECharts</span></div>
        <div class="hs-item"><span class="hs-k">数据口径</span><span class="hs-v">{{ YEARS[0] }}–{{ LATEST_YEAR }} 年年度报告</span></div>
        <div class="hs-item"><span class="hs-k">对标方法</span><span class="hs-v">行业 × 年度 × 指标 分位统计 + 方向调整评分</span></div>
      </div>
    </section>

    <!-- 关键数字 -->
    <section class="kpi-grid">
      <StatCard label="覆盖行业" :value="industryCount" unit="个" icon="industry" hint="证监会行业门类" />
      <StatCard label="样本上市公司" :value="companyCount" unit="家" icon="company" hint="真实财报数据" accent="purple" />
      <StatCard label="标准化指标" :value="indicatorCount" unit="项" icon="ruler" hint="六大维度" accent="up" />
      <StatCard label="数据年度" :value="`${YEARS[0]}–${LATEST_YEAR}`" icon="calendar" hint="5 个完整财年" accent="warn" />
      <StatCard
        label="报告数据点" :value="companyCount * indicatorCount * YEARS.length"
        unit="个" icon="number" hint="公司 × 指标 × 年度"
      />
    </section>

    <!-- 图表 -->
    <section class="two-col">
      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico"><AppIcon name="industry" :size="15" /></span>行业样本分布</div>
          <span class="card-sub">按行业统计样本公司数量</span>
        </div>
        <EChart :option="industryOption" height="272px" :empty="!store.industries.length" empty-text="字典加载中" filename="行业样本分布" />
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico"><AppIcon name="ruler" :size="15" /></span>指标维度覆盖</div>
          <span class="card-sub">六大维度指标数量</span>
        </div>
        <EChart :option="dimensionOption" height="272px" :empty="!store.indicators.length" empty-text="字典加载中" filename="指标维度覆盖" />
      </div>
    </section>

    <!-- 技术流程 -->
    <section class="card">
      <div class="card-hd">
        <div class="card-title"><span class="ico">🔄</span>系统核心流程</div>
        <span class="card-sub">数据 -> 计算 -> 对标 -> 生成 -> 校验 的完整闭环</span>
      </div>
      <div class="flow">
        <div v-for="(f, i) in FLOW" :key="f.n" class="flow-item">
          <div class="fi-head">
            <span class="fi-ico">{{ f.i }}</span>
            <span class="fi-n">{{ f.n }}</span>
          </div>
          <div class="fi-title">{{ f.t }}</div>
          <div class="fi-desc">{{ f.d }}</div>
          <span v-if="i < FLOW.length - 1" class="fi-arrow">→</span>
        </div>
      </div>
    </section>

    <!-- 指标字典 + 运行状态 -->
    <section class="two-col two-col--wide">
      <div class="card">
        <div class="card-hd">
          <div class="card-title"><span class="ico">📚</span>指标字典</div>
          <span class="card-sub">共 {{ indicatorCount }} 项标准化指标</span>
        </div>
        <div class="tbl-wrap">
          <table class="tbl">
            <thead>
              <tr><th>指标编码</th><th>指标名称</th><th>所属维度</th><th class="center">单位</th><th class="center">方向</th></tr>
            </thead>
            <tbody>
              <tr v-for="m in store.indicators" :key="m.code">
                <td class="mono muted">{{ m.code }}</td>
                <td>{{ m.name }}</td>
                <td><span class="tag mute">{{ m.dimension }}</span></td>
                <td class="center muted">{{ m.unit }}</td>
                <td class="center">
                  <span class="tag" :class="m.betterDirection === 'higher_better' ? 'ok' : 'warn'">
                    {{ m.betterDirection === 'higher_better' ? '↑' : '↓' }} {{ directionText(m.betterDirection) }}
                  </span>
                </td>
              </tr>
              <tr v-if="!store.indicators.length"><td colspan="5"><EmptyState title="指标字典加载中…" icon="empty" /></td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="side-col">
        <div class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">🩺</span>系统运行状态</div>
            <div class="card-tools">
              <button class="btn btn-ghost btn-xs" :disabled="store.healthChecking" @click="checkHealth">重新检测</button>
            </div>
          </div>
          <div class="health-badge" :class="store.healthState">
            <span class="dot" :class="store.healthState === 'ok' ? 'ok' : store.healthState === 'down' ? 'bad' : 'warn'"></span>
            {{ store.healthState === 'ok' ? '全部服务正常' : store.healthState === 'down' ? '后端服务未连接' : store.healthChecking ? '检测中…' : '服务状态异常' }}
          </div>
          <ul class="kv-list">
            <li v-for="r in healthRows" :key="r.k">
              <span class="kv-k">{{ r.k }}</span>
              <span class="kv-v" :class="{ 'text-down': !r.ok, 'text-up': r.ok }">{{ r.v }}</span>
            </li>
            <li v-if="!healthRows.length" class="muted">暂无状态信息, 请确认后端已启动(端口 8091)</li>
          </ul>
        </div>

        <div class="card">
          <div class="card-hd"><div class="card-title"><span class="ico">✅</span>质量保障</div></div>
          <ul class="check-list">
            <li>指标计算与行业统计全部后端完成, 口径固定可复现</li>
            <li>报告数字逐条溯源校验, 前端高亮"可溯源 / 待核对"</li>
            <li>百分位与排名按指标方向自适应(负债率越低越优)</li>
            <li>接口统一响应体 + 全局异常处理, 失败信息可读</li>
          </ul>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dash { display: flex; flex-direction: column; gap: var(--sp-5); }

/* Hero */
.hero {
  display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr); gap: var(--sp-6);
  padding: var(--sp-6);
  border-radius: var(--r-xl);
  background:
    radial-gradient(120% 160% at 100% 0%, rgba(74,137,224,.22) 0%, transparent 55%),
    linear-gradient(135deg, #14304f 0%, #12305a 45%, #17406f 100%);
  color: #dbe6f3;
  box-shadow: var(--sh-3);
}
.hero-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.hb { padding: 3px 10px; font-size: 11.5px; border-radius: var(--r-pill); background: rgba(255,255,255,.16); color: #eaf2fb; }
.hb-alt { background: rgba(111,168,255,.22); color: #cfe2ff; }
.hero h2 { font-size: 23px; color: #fff; letter-spacing: .3px; margin-bottom: 10px; }
.hero-desc { font-size: 13.5px; line-height: 1.85; color: #b9cde0; max-width: 70ch; }
.hero-desc strong { color: #fff; font-weight: 600; }
.hero-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.hero-actions .btn { background: #fff; color: var(--c-brand-700); box-shadow: none; }
.hero-actions .btn:hover { filter: none; background: #eaf2fb; }
.hero-actions .btn-ghost { background: rgba(255,255,255,.1); color: #dbe6f3; border-color: rgba(255,255,255,.28); }
.hero-actions .btn-ghost:hover { background: rgba(255,255,255,.18); color: #fff; }

.hero-side { display: flex; flex-direction: column; gap: 12px; justify-content: center; border-left: 1px solid rgba(255,255,255,.14); padding-left: var(--sp-5); }
.hs-item { display: flex; flex-direction: column; gap: 2px; }
.hs-k { font-size: 11.5px; color: #7fa3ca; }
.hs-v { font-size: 12.5px; color: #dbe6f3; line-height: 1.6; }

/* KPI */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: var(--sp-4); }

/* 两列 */
.two-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: var(--sp-5); }
.two-col--wide { grid-template-columns: minmax(0, 1.55fr) minmax(300px, 1fr); align-items: start; }
.side-col { display: flex; flex-direction: column; gap: var(--sp-5); }

/* 流程 */
.flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: var(--sp-3); }
.flow-item {
  position: relative; padding: 12px 14px;
  background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md);
  transition: all var(--dur) var(--ease);
}
.flow-item:hover { border-color: var(--c-brand-300); background: var(--c-brand-50); transform: translateY(-2px); }
.fi-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.fi-ico { font-size: 16px; }
.fi-n { font-family: var(--font-num); font-size: 12px; font-weight: 700; color: var(--c-brand-300); }
.fi-title { font-size: 13.5px; font-weight: 600; color: var(--c-brand-800); margin-bottom: 3px; }
.fi-desc { font-size: 12px; color: var(--c-text-3); line-height: 1.6; }
.fi-arrow { position: absolute; right: -11px; top: 50%; transform: translateY(-50%); color: var(--c-border-2); font-size: 14px; z-index: 1; }
.flow-item:last-child .fi-arrow { display: none; }

/* 运行状态 */
.health-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 12px; margin-bottom: 12px; font-size: 13px; font-weight: 500;
  border-radius: var(--r-md); background: var(--c-surface-2); color: var(--c-text-2);
}
.health-badge.ok { background: var(--c-up-bg); color: var(--c-up); }
.health-badge.down { background: var(--c-down-bg); color: var(--c-down); }
.health-badge.degraded { background: var(--c-warn-bg); color: var(--c-warn); }

.kv-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.kv-list li { display: flex; align-items: center; gap: 10px; padding: 7px 0; font-size: 13px; border-bottom: 1px dashed var(--c-border); }
.kv-list li:last-child { border-bottom: none; }
.kv-k { color: var(--c-text-3); width: 88px; flex: none; }
.kv-v { color: var(--c-text); font-weight: 500; word-break: break-all; }

.check-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 9px; }
.check-list li { position: relative; padding-left: 20px; font-size: 12.5px; color: var(--c-text-2); line-height: 1.65; }
.check-list li::before { content: '✓'; position: absolute; left: 0; top: 0; color: var(--c-up); font-weight: 700; }

@media (max-width: 1080px) {
  .hero { grid-template-columns: 1fr; }
  .hero-side { border-left: none; border-top: 1px solid rgba(255,255,255,.14); padding-left: 0; padding-top: var(--sp-4); }
  .two-col--wide { grid-template-columns: 1fr; }
}
</style>