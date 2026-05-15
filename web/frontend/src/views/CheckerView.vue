<script setup lang="ts">
import { ref } from 'vue'
import { apiPostRaw } from '@/api/client'
import type { CheckLayerResult, CheckResult } from '@/types/api'
import { useToast } from '@/composables/useToast'
import { copyText } from '@/utils/format'

const { toast } = useToast()
const title = ref('')
const body = ref('')
const localLayer = ref<CheckLayerResult | null>(null)
const adLawLayer = ref<CheckLayerResult | null>(null)
const overallSafe = ref<boolean | null>(null)
const showUuFrame = ref(false)
const uuFrameBlocked = ref(false)

const UU_CHECK_URL = 'https://uutool.cn/check-word/'

function combinedText() {
  return [title.value, body.value].filter(Boolean).join('\n\n')
}

function renderLayer(layer: CheckLayerResult) {
  const head = layer.safe
    ? `<p class="ok">✓ ${layer.label}：未命中</p>`
    : `<p class="bad">⚠ ${layer.label}：发现 ${layer.violations.length} 项</p>`
  const list = layer.violations.length
    ? `<p class="violations"><strong>命中：</strong>${layer.violations.join('、')}</p>`
    : ''
  const hint = layer.hint ? `<p class="muted small">${layer.hint}</p>` : ''
  return head + list + hint
}

async function run() {
  const text = combinedText()
  if (!text.trim()) return toast('请输入内容')
  try {
    const r = await apiPostRaw<CheckResult>('/api/check', { text })
    overallSafe.value = r.safe
    if (r.layers) {
      localLayer.value = r.layers.local
      adLawLayer.value = r.layers.ad_law
    } else {
      localLayer.value = {
        label: '本地·闲鱼词库',
        safe: r.safe,
        violations: r.violations || [],
      }
      adLawLayer.value = null
    }
  } catch {
    toast('检测失败')
  }
}

async function sanitize() {
  try {
    const [t, b] = await Promise.all([
      title.value
        ? apiPostRaw<CheckResult>('/api/check', { text: title.value })
        : null,
      body.value ? apiPostRaw<CheckResult>('/api/check', { text: body.value }) : null,
    ])
    if (t?.changed) title.value = t.sanitized
    if (b?.changed) body.value = b.sanitized
    localLayer.value = {
      label: '本地·闲鱼词库',
      safe: true,
      violations: [],
    }
    overallSafe.value = true
    toast('净化完成，建议重新点击「本地检测」')
  } catch {
    toast('净化失败')
  }
}

async function copyAll() {
  try {
    await copyText(`标题: ${title.value}\n\n${body.value}`)
    toast('已复制')
  } catch {
    toast('复制失败')
  }
}

async function openUutool() {
  const text = combinedText()
  if (!text.trim()) return toast('请先输入标题或正文')
  try {
    await copyText(text)
    window.open(UU_CHECK_URL, '_blank', 'noopener,noreferrer')
    showUuFrame.value = true
    toast('文案已复制。请在 UU 页面输入框粘贴，再点「开始检查」')
  } catch {
    window.open(UU_CHECK_URL, '_blank', 'noopener,noreferrer')
    toast('请手动复制文案到 UU 工具')
  }
}

function onUuFrameLoad(e: Event) {
  const iframe = e.target as HTMLIFrameElement
  try {
    const doc = iframe.contentDocument
    uuFrameBlocked.value = !doc || !doc.body?.innerHTML
  } catch {
    uuFrameBlocked.value = true
  }
}
</script>

<template>
  <div class="page checker-page">
    <p class="checker-external-hint muted">
      <strong>双重本地检测</strong>：闲鱼自建词库 + 广告法极限词参考（词表方向与
      <a
        :href="UU_CHECK_URL"
        target="_blank"
        rel="noopener noreferrer"
        class="external-link"
      >UU 闲鱼违禁词检测</a>
      公开说明一致，<em>非官网实时接口</em>）。
      最终发布前仍建议在 UU 官网再查一遍（结果以官网为准）。
    </p>

    <div class="checker-grid">
      <section class="card">
        <h3>待检测内容</h3>
        <label class="field">
          <span>标题</span>
          <input v-model="title" class="input" />
        </label>
        <label class="field">
          <span>正文</span>
          <textarea v-model="body" rows="10" class="input" />
        </label>
        <div class="row actions">
          <button type="button" class="btn primary" @click="run">本地检测</button>
          <button type="button" class="btn" @click="sanitize">一键净化</button>
          <button type="button" class="btn" @click="copyAll">复制</button>
          <button type="button" class="btn uu-btn" @click="openUutool">
            复制并打开 UU 官网
          </button>
        </div>
        <p class="muted small uu-steps">
          说明：浏览器安全策略下，无法自动填入 UU 页面内
          <code>#dataResource</code> 输入框，也无法读取官网检测结果。请使用「复制并打开
          UU 官网」后手动粘贴。
        </p>
      </section>

      <section class="card result-panel">
        <h3>检测结果</h3>

        <p
          v-if="overallSafe !== null"
          class="overall"
          :class="overallSafe ? 'ok' : 'warn'"
        >
          {{ overallSafe ? '综合：两项本地检测均通过' : '综合：至少一项未通过，请修改后再发' }}
        </p>

        <div v-if="localLayer" class="layer-card" v-html="renderLayer(localLayer)" />
        <div
          v-if="adLawLayer"
          class="layer-card ad-law"
          v-html="renderLayer(adLawLayer)"
        />

        <p v-if="localLayer === null" class="muted">输入内容后点击「本地检测」</p>

        <div class="uu-online-block">
          <div class="row head">
            <h4>UU 官网复检（人工）</h4>
            <button type="button" class="btn sm" @click="showUuFrame = !showUuFrame">
              {{ showUuFrame ? '收起嵌入页' : '展开嵌入页' }}
            </button>
          </div>
          <p class="muted small">
            在下方嵌入页或新标签页中粘贴文案 → 点击 UU「开始检查」→ 以官网标红结果为准。
          </p>
          <p v-if="uuFrameBlocked && showUuFrame" class="muted small frame-warn">
            嵌入页可能被 UU 站点限制，请优先使用「复制并打开 UU 官网」在新标签页操作。
          </p>
          <iframe
            v-show="showUuFrame"
            class="uu-frame"
            :src="UU_CHECK_URL"
            title="UU 闲鱼违禁词检测"
            referrerpolicy="no-referrer"
            @load="onUuFrameLoad"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.checker-external-hint {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--accent-soft, #fff4eb);
  border: 1px solid #ffd4b8;
  border-radius: var(--radius-sm, 10px);
  line-height: 1.65;
  font-size: 13px;
}
.checker-external-hint strong {
  color: var(--ink);
}
.checker-external-hint em {
  font-style: normal;
  color: var(--warn);
  font-weight: 600;
}
.actions {
  flex-wrap: wrap;
}
.uu-btn {
  border-color: var(--teal);
  color: var(--teal);
}
.uu-steps {
  margin-top: 12px;
  line-height: 1.5;
}
.uu-steps code {
  font-size: 11px;
  background: var(--paper-2);
  padding: 1px 5px;
  border-radius: 4px;
}
.overall {
  font-weight: 600;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
}
.overall.ok {
  background: var(--teal-soft, #e8faf3);
  color: var(--ok);
}
.overall.warn {
  background: #fffbeb;
  color: var(--warn);
}
.layer-card {
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--paper);
  font-size: 13px;
  line-height: 1.55;
}
.layer-card.ad-law {
  border-color: #dbeafe;
  background: #f8fafc;
}
.layer-card :deep(.ok) {
  color: var(--ok);
  font-weight: 600;
}
.layer-card :deep(.bad) {
  color: var(--danger);
  font-weight: 600;
}
.layer-card :deep(.violations) {
  margin-top: 6px;
}
.uu-online-block {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}
.uu-online-block h4 {
  font-size: 14px;
  margin: 0;
}
.uu-frame {
  width: 100%;
  height: min(520px, 55vh);
  margin-top: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: #fff;
}
.frame-warn {
  color: var(--warn);
  margin-top: 8px;
}
.external-link {
  color: var(--teal, #00b578);
  font-weight: 600;
  text-decoration: none;
}
.external-link:hover {
  text-decoration: underline;
}
</style>
