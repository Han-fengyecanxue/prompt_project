<script setup>
import { ref, watch, onMounted } from 'vue'
import { api, YEARS } from '../api'

const props = defineProps({ company: Object })
const year = ref(2025)

const generating = ref(false)
const err = ref('')
const report = ref(null)          // 最近生成的简报
const question = ref('')
const chatting = ref(false)
const chatHistory = ref([])       // [{role, content}]

async function generate() {
  if (!props.company) return
  generating.value = true
  err.value = ''
  try {
    report.value = await api.aiReport({ companyId: props.company.companyId, fiscalYear: year.value })
  } catch (e) {
    err.value = e.message
  } finally {
    generating.value = false
  }
}

async function send() {
  const q = question.value.trim()
  if (!q || !props.company) return
  chatting.value = true
  err.value = ''
  try {
    const history = chatHistory.value.map(t => ({ role: t.role, content: t.content }))
    const ans = await api.aiChat({
      companyId: props.company.companyId,
      fiscalYear: year.value,
      question: q,
      history
    })
    chatHistory.value.push({ role: 'user', content: q })
    chatHistory.value.push({ role: 'assistant', content: ans.aiAnswer })
    question.value = ''
  } catch (e) {
    err.value = e.message
  } finally {
    chatting.value = false
  }
}

watch(() => props.company, () => { report.value = null; chatHistory.value = [] })
onMounted(() => {})

// ---------- 轻量 Markdown 渲染(安全: 先转义再排版, 不注入 HTML) ----------
function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
function inlineMd(s) {
  return s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/`(.+?)`/g, '<code>$1</code>')
}
function mdToHtml(text) {
  const lines = esc(text).split('\n')
  const out = []
  for (const raw of lines) {
    const line = raw.trimEnd()
    if (!line.trim()) { out.push('<div class="mdp"></div>'); continue }
    const h = line.match(/^(#{1,4})\s+(.*)/)
    if (h) {
      const lv = Math.min(h[1].length + 2, 6)
      out.push(`<div class="mdh h${lv}">${inlineMd(h[2])}</div>`)
    } else if (/^\s*[-*•]\s+/.test(line)) {
      out.push(`<div class="mdli">• ${inlineMd(line.replace(/^\s*[-*•]\s+/, ''))}</div>`)
    } else if (/^\s*\d+[.、]\s+/.test(line)) {
      out.push(`<div class="mdli">${inlineMd(line)}</div>`)
    } else {
      out.push(`<div class="mdp">${inlineMd(line)}</div>`)
    }
  }
  return out.join('')
}
</script>

<template>
  <div v-if="!company" class="card muted">请先在「公司查询」页选择一家公司。</div>

  <div v-else>
    <div class="card">
      <div class="row">
        <h2 style="font-size:18px;color:#1f3b63">
          AI 解读 <span class="muted">{{ company.stockName }} {{ company.stockCode }}</span>
        </h2>
        <select v-model.number="year" style="margin-left:auto">
          <option v-for="y in YEARS" :key="y" :value="y">{{ y }} 年报</option>
        </select>
        <button :disabled="generating" @click="generate">
          {{ generating ? '生成中…' : '生成解读简报' }}
        </button>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
      <p class="muted mt">
        解读由三层 Prompt 驱动(角色设定 → 数据注入 → 输出约束); 注入的指标与行业对标数据均由系统精确计算, 要求模型不得编造数字。
      </p>
    </div>

    <!-- 简报 -->
    <div class="card mt" v-if="report">
      <h3>📄 财报解读简报({{ year }} 年)</h3>
      <div class="mdbody mt" v-html="mdToHtml(report.aiAnswer)"></div>
      <p class="muted mt">⚠️ 本报告由大模型基于注入数据生成, 仅供学习研究, 不构成投资建议</p>
    </div>

    <!-- 对话 -->
    <div class="card mt">
      <h3>💬 追问对话(上下文感知)</h3>
      <div class="chatbox mt">
        <div v-for="(t, i) in chatHistory" :key="i" class="msg" :class="t.role">
          <div class="bubble" v-if="t.role === 'user'">{{ t.content }}</div>
          <div class="bubble md" v-else v-html="mdToHtml(t.content)"></div>
        </div>
        <p v-if="!chatHistory.length" class="muted">可提问如: 「ROE 和毛利率在行业里处于什么水平?」「资产负债率风险大吗?」</p>
      </div>
      <div class="row mt">
        <input v-model="question" placeholder="输入问题…" style="flex:1" @keyup.enter="send" />
        <button :disabled="chatting || !question.trim()" @click="send">{{ chatting ? '回答中…' : '发送' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chatbox { max-height: 340px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.msg.user { align-self: flex-end; }
.msg.assistant { align-self: flex-start; }
.bubble {
  max-width: 88%;
  padding: 9px 13px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}
.user .bubble { background: #1f3b63; color: #fff; }
.assistant .bubble { background: #eef2f8; color: #333; }
.bubble.md { white-space: normal; }

/* 轻量 Markdown 排版 */
.mdbody { line-height: 1.85; font-size: 14px; }
.mdbody .mdp { margin: 2px 0; white-space: pre-wrap; }
.mdbody .mdli { margin: 2px 0 2px 2px; }
.mdbody .mdh { font-weight: 700; color: #1f3b63; margin: 10px 0 4px; }
.mdbody .h4 { font-size: 16px; }
.mdbody .h5 { font-size: 15px; }
.mdbody .h6 { font-size: 14px; }
.mdbody b { color: #1e7e34; }
</style>
