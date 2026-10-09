<script setup>
/**
 * AI 解读
 * 核心展示点: "数据注入 -> 模型生成 -> 数值溯源校验" 的闭环
 * - 生成过程分步提示, 让评审看清系统在整个链路里做了什么
 * - 报告中的数字与系统计算数据比对, 可溯源标绿 / 待核对标黄
 * - 附三层 Prompt 模板展示与历史报告记录
 */
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { api } from '../api'
import { store, toast } from '../store'
import EmptyState from '../components/EmptyState.vue'
import AppDrawer from '../components/AppDrawer.vue'
import { renderMarkdown, verifyNumbers, collectKnownNumbers } from '../utils/markdown'
import { fmtDateTime, copyText } from '../utils/format'

defineOptions({ name: 'AiView' })
const emit = defineEmits(['select', 'navigate'])

const company = computed(() => store.selectedCompany)
const year = computed(() => store.year)

const generating = ref(false)
const genStep = ref(-1)
const err = ref('')
const report = ref(null)

const question = ref('')
const chatting = ref(false)
const chatHistory = ref([])

const templates = ref([])
const history = ref([])
const historyLoading = ref(false)

const benchmark = ref(null)
const profile = ref(null)
const showHighlight = ref(true)
const chatScroll = ref(null)

const GEN_STEPS = [
  { t: '读取指标与行业对标数据', d: '从 financial_indicator / industry_benchmark 取值' },
  { t: '组装三层 Prompt', d: '角色设定 + 数据注入(JSON) + 输出约束' },
  { t: '调用大模型生成解读', d: '按固定六章节结构输出, 禁止编造数字' },
  { t: '数值溯源校验', d: '逐个数字比对系统计算值, 标记可疑项' }
]

const SUGGESTIONS = [
  'ROE 和毛利率在行业里处于什么水平?',
  '资产负债率风险大吗? 现金流质量如何?',
  '这家公司的成长性由哪些指标支撑?',
  '当前估值在行业中偏贵还是偏便宜?',
  '综合来看, 最需要关注的风险点是什么?'
]

/** 可溯源数值集合(对应"当前注入年度" store.year) */
const knownNumbers = computed(() => collectKnownNumbers(profile.value, benchmark.value))

/**
 * 溯源高亮/统计只在"被校验文本的年度 == 当前注入数据的年度"时成立。
 * 历史记录或旧对话可能来自别的财年, 若强行比对会大面积误报"待人工核对"。
 */
const yearMatches = (y) => y == null || Number(y) === Number(year.value)

function mdOf(text, y) {
  const ok = yearMatches(y)
  return renderMarkdown(text, {
    highlight: showHighlight.value && ok,
    known: ok ? knownNumbers.value : []
  })
}
function checkOf(text, y) {
  if (!yearMatches(y)) return null
  return verifyNumbers(text, knownNumbers.value)
}

/** 报告溯源校验结果(年度不一致时不做校验, 避免误报) */
const reportCheck = computed(() => {
  if (!report.value || !report.value.aiAnswer) return null
  if (!yearMatches(report.value.fiscalYear)) return null
  const local = verifyNumbers(report.value.aiAnswer, knownNumbers.value)
  return {
    ...local,
    backendAccuracy: report.value.numericAccuracy,
    backendSuspicious: report.value.suspiciousCount,
    model: report.value.modelName || null
  }
})

/** 报告来自其他财年(例如切了财年但没重新生成): 提示而非误报 */
const reportStale = computed(() =>
  !!(report.value && report.value.fiscalYear != null && !yearMatches(report.value.fiscalYear))
)

/* ------------------------------------------------------- 历史记录抽屉 */
const detailOpen = ref(false)
const detailItem = ref(null)
const detailCheck = computed(() => {
  const h = detailItem.value
  if (!h || !h.aiAnswer) return null
  if (!yearMatches(h.fiscalYear)) return null
  return verifyNumbers(h.aiAnswer, knownNumbers.value)
})

function openDetail(h) {
  detailItem.value = h
  detailOpen.value = true
}
/** 把历史记录载入到主面板 */
function loadToPanel(h) {
  if (h.reportType === 'chat') {
    chatHistory.value.push({ role: 'user', content: h.userQuestion || '(历史提问)', history: true, year: h.fiscalYear })
    chatHistory.value.push({ role: 'assistant', content: h.aiAnswer || '', history: true, year: h.fiscalYear })
    toast('已载入历史对话', 'info')
  } else {
    report.value = h
    toast('已载入历史简报到主面板', 'info')
  }
  detailOpen.value = false
}

async function loadContext() {
  if (!company.value || !company.value.companyId) return
  try {
    const [p, b] = await Promise.all([
      api.profile(company.value.companyId, year.value),
      api.benchmark(company.value.companyId, year.value)
    ])
    profile.value = p
    benchmark.value = b
  } catch {
    profile.value = null
    benchmark.value = null
  }
}

async function loadSide() {
  try {
    const t = await api.templates()
    templates.value = t || []
  } catch { templates.value = [] }
  await loadHistory()
}

async function loadHistory() {
  if (!company.value) return
  historyLoading.value = true
  try {
    const data = await api.aiReports({ companyId: company.value.companyId, page: 1, size: 6 })
    history.value = data.list || []
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

async function generate() {
  if (!company.value) return
  generating.value = true
  err.value = ''
  report.value = null
  genStep.value = 0
  const timers = [
    setTimeout(() => { if (generating.value) genStep.value = 1 }, 260),
    setTimeout(() => { if (generating.value) genStep.value = 2 }, 760),
    setTimeout(() => { if (generating.value) genStep.value = 3 }, 1600)
  ]
  try {
    report.value = await api.aiReport({ companyId: company.value.companyId, fiscalYear: year.value })
    toast('解读简报生成完成', 'ok')
    loadHistory()
  } catch (e) {
    err.value = e.message
    toast(e.message, 'error', 5000)
  } finally {
    timers.forEach(clearTimeout)
    generating.value = false
    genStep.value = -1
  }
}

async function send() {
  const q = question.value.trim()
  if (!q || !company.value || chatting.value) return
  err.value = ''
  const historyPayload = chatHistory.value
    .filter(t => t.role === 'user' || t.role === 'assistant')
    .map(t => ({ role: t.role, content: t.content }))
  const turnYear = year.value
  chatHistory.value.push({ role: 'user', content: q, year: turnYear })
  question.value = ''
  const pending = { role: 'assistant', content: '', pending: true, year: turnYear }
  chatHistory.value.push(pending)
  chatting.value = true
  await scrollChat()
  try {
    const ans = await api.aiChat({
      companyId: company.value.companyId,
      fiscalYear: year.value,
      question: q,
      history: historyPayload
    })
    pending.content = ans.aiAnswer || '(模型未返回内容)'
    pending.pending = false
  } catch (e) {
    chatHistory.value = chatHistory.value.filter(t => t !== pending)
    chatHistory.value.push({ role: 'user', content: q, failed: true, year: turnYear })
    err.value = e.message
    toast(e.message, 'error', 5000)
  } finally {
    chatting.value = false
    scrollChat()
  }
}

async function scrollChat() {
  await nextTick()
  if (chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight
}

function askSuggestion(s) {
  question.value = s
  send()
}

function clearChat() {
  chatHistory.value = []
  toast('已清空当前对话', 'info', 1800)
}

async function copyReport() {
  if (!report.value) return
  const ok = await copyText(report.value.aiAnswer || '')
  toast(ok ? '报告已复制到剪贴板' : '复制失败, 请手动选择文本', ok ? 'ok' : 'warn')
}

function exportMd() {
  if (!report.value) return
  const head = `# ${company.value.stockName}(${company.value.stockCode}) ${year.value} 年报 AI 解读简报\n\n`
    + `> 生成时间: ${fmtDateTime(report.value.createTime || new Date())} ｜ 数值溯源准确率: ${reportCheck.value ? reportCheck.value.ratio : '—'}%\n\n`
  const blob = new Blob([head + (report.value.aiAnswer || '')], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${company.value.stockName}_${year.value}_AI解读简报.md`
  a.click()
  URL.revokeObjectURL(url)
  toast('已导出 Markdown 报告', 'ok')
}

const doPrint = () => window.print()

watch(company, () => {
  report.value = null
  chatHistory.value = []
  loadContext()
  loadHistory()
})
watch(year, loadContext)

onMounted(() => { loadContext(); loadSide() })
</script>

<template>
  <div class="ai-view">
    <EmptyState
      v-if="!company"
      icon="⚠️" title="尚未选择公司"
      desc="AI 解读需要先指定分析对象。请前往「公司查询」选择一家公司, 或使用顶栏右侧的公司选择器。"
      action-text="前往公司查询" @action="emit('navigate', 'list')"
    />

    <div v-else class="ai-layout">
      <!-- 主列 -->
      <div class="ai-main">
        <!-- 生成控制 -->
        <div class="card">
          <div class="card-hd">
            <div class="card-title">
              <span class="ico">💡</span>AI 财报解读
              <span class="tag mute">{{ company.stockName }} · {{ year }} 年报</span>
            </div>
            <div class="card-tools">
              <button class="btn btn-ghost btn-sm" @click="emit('navigate', 'profile')">← 返回画像</button>
              <button class="btn" :disabled="generating" @click="generate">
                {{ generating ? '生成中…' : (report ? '重新生成简报' : '生成解读简报') }}
              </button>
            </div>
          </div>

          <div class="card-bd">
            <p class="muted">
              解读由<strong>三层 Prompt</strong>驱动: 角色设定(资深财务分析师) → 数据注入(系统精确计算的指标与行业对标 JSON)
              → 输出约束(固定六章节 / 禁止编造数字 / 800 字以内)。模型只能使用注入数据, 因此结论可复现、可审计。
            </p>

            <!-- 生成进度 -->
            <div v-if="generating" class="gen-steps">
              <div v-for="(s, i) in GEN_STEPS" :key="i" class="gen-step" :class="{ on: genStep >= i, doing: genStep === i }">
                <span class="gs-dot">{{ genStep > i ? '✓' : genStep === i ? '●' : '○' }}</span>
                <div class="gs-body">
                  <div class="gs-title">{{ s.t }}</div>
                  <div class="gs-desc muted">{{ s.d }}</div>
                </div>
              </div>
            </div>

            <p v-if="err" class="alert mt-3"><span>⛔</span><span>{{ err }}</span></p>
          </div>
        </div>

        <!-- 报告 -->
        <div v-if="report" class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">📄</span>财报解读简报</div>
            <span class="card-sub">{{ year }} 年报 · 生成于 {{ fmtDateTime(report.createTime || new Date()) }}</span>
            <div class="card-tools">
              <label class="switch" title="高亮报告中的数字, 绿色 = 可在系统数据中溯源">
                <input v-model="showHighlight" type="checkbox" />
                <span>数值溯源高亮</span>
              </label>
              <button class="btn btn-ghost btn-sm" @click="copyReport">复制</button>
              <button class="btn btn-ghost btn-sm" @click="exportMd">导出 MD</button>
              <button class="btn btn-ghost btn-sm" @click="doPrint">打印</button>
            </div>
          </div>

          <div v-if="reportCheck" class="trace-bar">
            <div class="tb-item">
              <span class="tb-num" :class="reportCheck.ratio >= 90 ? 'text-up' : reportCheck.ratio >= 70 ? '' : 'text-down'">
                {{ reportCheck.ratio }}%
              </span>
              <span class="tb-lab">数值可溯源率</span>
            </div>
            <div class="tb-item"><span class="tb-num">{{ reportCheck.matched }}</span><span class="tb-lab">可溯源数字</span></div>
            <div class="tb-item"><span class="tb-num" :class="{ 'text-down': reportCheck.missing > 0 }">{{ reportCheck.missing }}</span><span class="tb-lab">待人工核对</span></div>
            <div class="tb-item" v-if="reportCheck.backendAccuracy !== null && reportCheck.backendAccuracy !== undefined">
              <span class="tb-num">{{ reportCheck.backendAccuracy }}%</span><span class="tb-lab">后端校验准确率</span>
            </div>
            <div class="tb-bar">
              <div class="bar"><i :style="{ width: `${reportCheck.ratio}%`, background: reportCheck.ratio >= 90 ? 'var(--c-up)' : 'var(--c-warn)' }"></i></div>
            </div>
          </div>

          <div v-if="reportCheck && reportCheck.missingList.length" class="alert warn mt-3">
            <span>⚠️</span>
            <span>
              以下数字未能在系统计算数据中匹配到出处, 建议人工核对:
              <b class="mono">{{ reportCheck.missingList.join('、') }}</b>
              <br class="muted" />
              (可能来自模型对表述的合理改写, 也可能提示存在幻觉风险, 这正是本系统要暴露的问题)
            </span>
          </div>

          <div v-if="reportStale" class="alert info mt-3">
            <span>ℹ️</span>
            <span>该简报生成于 <b>{{ report.fiscalYear }}</b> 年, 而当前注入数据为 <b>{{ year }}</b> 年,
              两者年度不一致, 因此<strong>不启用数值溯源高亮</strong>（避免误报）。如需校验, 请在右上角切回对应财年后重新生成。</span>
          </div>

          <div class="md-body" v-html="mdOf(report.aiAnswer, report.fiscalYear)"></div>

          <p class="muted mt-4 disclaimer">
            ⚠️ 本报告由大模型基于系统注入数据生成, 全部数值可由「财务画像」页复核; 仅供学习研究, 不构成投资建议。
          </p>
        </div>

        <!-- 对话 -->
        <div class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">💬</span>追问对话</div>
            <span class="card-sub">携带此前对话上下文, 同样受"禁止编造数字"约束</span>
            <div class="card-tools">
              <button class="btn btn-ghost btn-sm" :disabled="!chatHistory.length" @click="clearChat">清空对话</button>
            </div>
          </div>

          <div ref="chatScroll" class="chatbox">
            <div v-if="!chatHistory.length" class="chat-empty">
              <p class="muted">可以这样提问 —— 点击直接发送:</p>
              <div class="sugs">
                <button v-for="s in SUGGESTIONS" :key="s" class="chip" @click="askSuggestion(s)">{{ s }}</button>
              </div>
            </div>

            <div v-for="(t, i) in chatHistory" :key="i" class="msg" :class="t.role">
              <div class="bubble" :class="{ md: t.role === 'assistant' }">
                <template v-if="t.pending">
                  <span class="typing"><i></i><i></i><i></i></span>
                  <span class="muted">模型正在基于注入数据作答…</span>
                </template>
                <template v-else-if="t.role === 'user'">{{ t.content }}</template>
                <template v-else>
                  <span v-if="t.history" class="tag mute hist">历史记录</span>
                  <span v-if="t.year && t.year !== year" class="tag warn hist">生成于 {{ t.year }} 年</span>
                  <div v-html="mdOf(t.content, t.year)"></div>
                  <div v-if="checkOf(t.content, t.year)" class="bubble-foot muted">
                    数值可溯源 {{ checkOf(t.content, t.year).ratio }}%
                    （{{ checkOf(t.content, t.year).matched }}/{{ checkOf(t.content, t.year).total }}）
                  </div>
                  <div v-else class="bubble-foot muted">年度与当前注入数据不一致, 未做溯源校验</div>
                </template>
              </div>
            </div>
          </div>

          <div class="ask-row">
            <input
              v-model="question" placeholder="输入追问问题… (Enter 发送)"
              :disabled="chatting" @keyup.enter="send"
            />
            <button class="btn" :disabled="chatting || !question.trim()" @click="send">
              {{ chatting ? '回答中…' : '发送' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 侧栏 -->
      <aside class="ai-side">
        <div class="card">
          <div class="card-hd"><div class="card-title"><span class="ico">🧩</span>三层 Prompt 模板</div></div>
          <div v-if="!templates.length" class="muted">模板加载中…</div>
          <div v-else class="tpl-list">
            <div v-for="(t, i) in templates" :key="t.templateId || i" class="tpl">
              <div class="tpl-head">
                <span class="tpl-idx">{{ ['①', '②', '③'][i] || `#${i + 1}` }}</span>
                <span class="tpl-type">{{ t.templateType }}</span>
                <span class="tag mute">v{{ t.version || '1.0' }}</span>
              </div>
              <div class="tpl-body">{{ t.templateContent }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="card-title"><span class="ico">🕘</span>历史记录</div>
            <div class="card-tools">
              <button class="btn btn-ghost btn-xs" :disabled="historyLoading" @click="loadHistory">刷新</button>
            </div>
          </div>
          <p v-if="historyLoading" class="muted">加载中…</p>
          <EmptyState v-else-if="!history.length" icon="🗂️" title="暂无历史记录" desc="生成的简报与对话会自动保存到 ai_report 表。" />
          <ul v-else class="hist-list">
            <li v-for="h in history" :key="h.reportId">
              <button class="hist-item" @click="openDetail(h)">
                <span class="hi-top">
                  <span class="tag" :class="h.reportType === 'chat' ? 'purple' : ''">{{ h.reportType === 'chat' ? '对话' : '简报' }}</span>
                  <span class="mono muted">{{ h.fiscalYear }} 年</span>
                  <span class="muted hi-time">{{ fmtDateTime(h.createTime) }}</span>
                </span>
                <span class="hi-text">{{ (h.userQuestion || h.aiAnswer || '').slice(0, 62) }}…</span>
                <span class="hi-meta muted">
                  准确率 {{ h.numericAccuracy != null ? h.numericAccuracy + '%' : '—' }}
                  · 可疑数字 {{ h.suspiciousCount != null ? h.suspiciousCount : '—' }}
                  · 点击查看全文
                </span>
              </button>
            </li>
          </ul>
        </div>

        <div class="card">
          <div class="card-hd"><div class="card-title"><span class="ico">🔍</span>溯源校验说明</div></div>
          <ul class="note-list">
            <li><span class="num-hit demo">28.56</span> 绿色: 该数字能在系统计算的指标 / 对标数据中找到出处。</li>
            <li><span class="num-miss demo">99.9</span> 黄色: 未匹配到出处, 提示可能为幻觉, 需人工核对。</li>
            <li>校验在<strong>浏览器端</strong>完成, 与后端 <code>numeric_accuracy</code> 字段互为印证。</li>
          </ul>
        </div>
      </aside>
    </div>

    <!-- 历史记录详情抽屉 -->
    <AppDrawer
      v-model="detailOpen"
      :title="detailItem ? (detailItem.reportType === 'chat' ? '历史对话详情' : '历史简报详情') : ''"
      :subtitle="detailItem ? `${company ? company.stockName : ''} · ${detailItem.fiscalYear} 年报 · ${fmtDateTime(detailItem.createTime)}` : ''"
      width="620px"
    >
      <template v-if="detailItem">
        <div class="dd-meta">
          <span class="tag" :class="detailItem.reportType === 'chat' ? 'purple' : ''">
            {{ detailItem.reportType === 'chat' ? '追问对话' : '解读简报' }}
          </span>
          <span v-if="detailItem.numericAccuracy != null" class="tag ok">
            后端校验准确率 {{ detailItem.numericAccuracy }}%
          </span>
          <span v-if="detailItem.suspiciousCount != null" class="tag"
                :class="detailItem.suspiciousCount > 0 ? 'warn' : 'mute'">
            可疑数字 {{ detailItem.suspiciousCount }}
          </span>
        </div>

        <div v-if="detailItem.userQuestion" class="dd-q">
          <span class="muted">提问</span>
          <p>{{ detailItem.userQuestion }}</p>
        </div>

        <div v-if="detailCheck" class="trace-bar">
          <div class="tb-item">
            <span class="tb-num" :class="detailCheck.ratio >= 90 ? 'text-up' : detailCheck.ratio >= 70 ? '' : 'text-down'">
              {{ detailCheck.ratio }}%
            </span>
            <span class="tb-lab">数值可溯源率</span>
          </div>
          <div class="tb-item"><span class="tb-num">{{ detailCheck.matched }}</span><span class="tb-lab">可溯源数字</span></div>
          <div class="tb-item"><span class="tb-num" :class="{ 'text-down': detailCheck.missing > 0 }">{{ detailCheck.missing }}</span><span class="tb-lab">待人工核对</span></div>
        </div>
        <div v-else class="alert info mt-3">
          <span>ℹ️</span>
          <span>该记录生成于 {{ detailItem.fiscalYear }} 年, 与当前注入数据年度({{ year }} 年)不一致,
            故未做数值溯源校验。</span>
        </div>

        <div class="md-body" v-html="mdOf(detailItem.aiAnswer, detailItem.fiscalYear)"></div>
      </template>

      <template #footer>
        <button class="btn btn-ghost btn-sm" @click="copyText(detailItem && detailItem.aiAnswer || '').then(ok => toast(ok ? '已复制' : '复制失败', ok ? 'ok' : 'warn'))">复制全文</button>
        <button class="btn btn-sm" @click="loadToPanel(detailItem)">载入到主面板</button>
      </template>
    </AppDrawer>
  </div>
</template>

<style scoped>
.ai-layout { display: grid; grid-template-columns: minmax(0, 1fr) 336px; gap: var(--sp-5); align-items: start; }
.ai-main, .ai-side { display: flex; flex-direction: column; gap: var(--sp-5); min-width: 0; }

/* 生成进度 */
.gen-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: var(--sp-3); margin-top: var(--sp-4); }
.gen-step {
  display: flex; gap: 9px; padding: 10px 12px;
  background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md);
  opacity: .55; transition: all .25s var(--ease);
}
.gen-step.on { opacity: 1; border-color: var(--c-brand-300); background: var(--c-brand-50); }
.gen-step.doing { box-shadow: 0 0 0 3px rgba(74,137,224,.14); }
.gs-dot { color: var(--c-brand-500); font-size: 12px; line-height: 1.6; }
.gs-title { font-size: 12.5px; font-weight: 600; color: var(--c-brand-800); }
.gs-desc { font-size: 11.5px; }

/* 溯源统计条 */
.trace-bar {
  display: flex; align-items: center; gap: var(--sp-5); flex-wrap: wrap;
  margin: var(--sp-3) 0; padding: 12px 16px;
  background: linear-gradient(90deg, rgba(47,111,208,.06), rgba(47,111,208,.01));
  border: 1px solid var(--c-border); border-radius: var(--r-md);
}
.tb-item { display: flex; flex-direction: column; line-height: 1.3; }
.tb-num { font-family: var(--font-num); font-size: 19px; font-weight: 700; color: var(--c-brand-800); }
.tb-lab { font-size: 11.5px; color: var(--c-text-3); }
.tb-bar { flex: 1 1 160px; min-width: 120px; }

/* Markdown 渲染区 */
.md-body { margin-top: var(--sp-4); font-size: 13.8px; line-height: 1.9; color: var(--c-text); }
.md-body :deep(.md-h) { font-weight: 700; color: var(--c-brand-800); margin: 20px 0 8px; padding-bottom: 5px; border-bottom: 1px solid var(--c-border); }
.md-body :deep(.md-h1) { font-size: 18px; }
.md-body :deep(.md-h2) { font-size: 15.5px; }
.md-body :deep(.md-h3) { font-size: 14.5px; }
.md-body :deep(.md-h4) { font-size: 13.8px; }
.md-body :deep(.md-p) { margin: 5px 0; }
.md-body :deep(.md-ul), .md-body :deep(.md-ol) { margin: 6px 0 6px 22px; padding: 0; }
.md-body :deep(li) { margin: 4px 0; }
.md-body :deep(b) { color: var(--c-brand-700); }
.md-body :deep(code) { padding: 1px 5px; font-size: 12.5px; background: var(--c-surface-3); border-radius: 4px; font-family: Consolas, monospace; }
.md-body :deep(.md-quote) { margin: 8px 0; padding: 6px 12px; border-left: 3px solid var(--c-brand-300); background: var(--c-brand-50); color: var(--c-text-2); }
.md-body :deep(.md-hr) { border: none; border-top: 1px dashed var(--c-border); margin: 14px 0; }
.md-body :deep(.md-table-wrap) { overflow-x: auto; margin: 10px 0; }
.md-body :deep(.md-table) { width: 100%; border-collapse: collapse; font-size: 12.8px; }
.md-body :deep(.md-table th), .md-body :deep(.md-table td) { padding: 6px 10px; border: 1px solid var(--c-border); text-align: left; }
.md-body :deep(.md-table th) { background: var(--c-surface-2); color: var(--c-brand-800); }

/* 数值溯源标记(全局类, 需 deep) */
.md-body :deep(.num-hit),
.bubble :deep(.num-hit) {
  padding: 0 3px; border-radius: 3px;
  background: var(--c-up-bg); color: var(--c-up); font-weight: 600;
  border-bottom: 1px dashed var(--c-up);
}
.md-body :deep(.num-miss),
.bubble :deep(.num-miss) {
  padding: 0 3px; border-radius: 3px;
  background: var(--c-warn-bg); color: #8a5a05; font-weight: 600;
  border-bottom: 1px dashed var(--c-warn);
}
.note-list .demo { display: inline-block; margin-right: 4px; }
.num-hit.demo { background: var(--c-up-bg); color: var(--c-up); }
.num-miss.demo { background: var(--c-warn-bg); color: #8a5a05; }

.disclaimer { padding-top: 10px; border-top: 1px dashed var(--c-border); }

/* 开关 */
.switch { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--c-text-2); cursor: pointer; }
.switch input { width: 14px; height: 14px; min-height: 0; accent-color: var(--c-brand-500); }

/* 对话 */
.chatbox { max-height: 380px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding: var(--sp-3) 2px; }
.chat-empty { padding: 8px 2px 4px; }
.sugs { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.msg { display: flex; }
.msg.user { justify-content: flex-end; }
.msg.assistant { justify-content: flex-start; }
.bubble {
  max-width: 88%; padding: 9px 13px; font-size: 13.5px; line-height: 1.75;
  border-radius: 12px; word-break: break-word;
}
.msg.user .bubble { background: linear-gradient(180deg, var(--c-brand-500), var(--c-brand-600)); color: #fff; border-bottom-right-radius: 4px; }
.msg.assistant .bubble { background: var(--c-surface-2); border: 1px solid var(--c-border); color: var(--c-text); border-bottom-left-radius: 4px; }
.bubble-foot { margin-top: 6px; padding-top: 5px; border-top: 1px dashed var(--c-border); font-size: 11px; }
.hist { margin-bottom: 5px; }

.typing { display: inline-flex; gap: 3px; margin-right: 8px; vertical-align: middle; }
.typing i { width: 5px; height: 5px; border-radius: 50%; background: var(--c-brand-400); animation: blink 1.2s infinite; }
.typing i:nth-child(2) { animation-delay: .2s; }
.typing i:nth-child(3) { animation-delay: .4s; }
@keyframes blink { 0%, 60%, 100% { opacity: .25 } 30% { opacity: 1 } }

.ask-row { display: flex; gap: 10px; margin-top: var(--sp-3); }
.ask-row input { flex: 1; }

/* 侧栏 */
.tpl-list { display: flex; flex-direction: column; gap: 10px; }
.tpl { padding: 10px 12px; background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md); }
.tpl-head { display: flex; align-items: center; gap: 7px; margin-bottom: 6px; }
.tpl-idx { color: var(--c-brand-400); font-size: 13px; }
.tpl-type { font-size: 12.5px; font-weight: 600; color: var(--c-brand-700); }
.tpl-body { font-size: 11.8px; color: var(--c-text-2); line-height: 1.7; max-height: 118px; overflow-y: auto; white-space: pre-wrap; }

.hist-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.hist-item {
  display: flex; flex-direction: column; gap: 5px; width: 100%; text-align: left;
  padding: 9px 11px; font-family: inherit;
  background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md);
  cursor: pointer; transition: all var(--dur) var(--ease);
}
.hist-item:hover { border-color: var(--c-brand-300); background: var(--c-brand-50); }
.hi-top { display: flex; align-items: center; gap: 7px; }
.hi-time { margin-left: auto; font-size: 11px; }
.hi-text { font-size: 12.2px; color: var(--c-text-2); line-height: 1.55; }
.hi-meta { font-size: 11px; }

.note-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 9px; }
.note-list li { font-size: 12.2px; color: var(--c-text-2); line-height: 1.7; }
.note-list code { padding: 1px 5px; background: var(--c-surface-3); border-radius: 4px; font-size: 11.5px; }

/* 抽屉内容 */
.dd-meta { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3); }
.dd-q { padding: 9px 12px; background: var(--c-surface-2); border: 1px solid var(--c-border); border-radius: var(--r-md); margin-bottom: var(--sp-3); }
.dd-q p { margin-top: 3px; font-size: 13px; color: var(--c-text); }

@media (max-width: 1180px) {
  .ai-layout { grid-template-columns: 1fr; }
}
</style>
