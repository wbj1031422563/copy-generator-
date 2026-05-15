<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiPost } from '@/api/client'
import type { GenerateResult, StyleKey } from '@/types/api'
import { useAppStore, useChatStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'
import VariantCard from '@/components/VariantCard.vue'
import CompareModal from '@/components/CompareModal.vue'
import UiButton from '@/components/ui/UiButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { fmtDate } from '@/utils/format'

const app = useAppStore()
const chat = useChatStore()
const { toast } = useToast()
const router = useRouter()

const input = ref('')
const style = ref<StyleKey>('comprehensive')
const versionCount = ref(3)
const llmProvider = ref('')
const generating = ref(false)
const compareOpen = ref(false)

const QUICK = [
  { label: '目标检测 · YOLO', kw: '目标检测 YOLO 计算机视觉' },
  { label: 'CCF · 深度学习', kw: 'CCF论文 深度学习' },
  { label: 'NLP · 大模型', kw: 'NLP 大语言模型 LLM' },
  { label: '医学图像 AI', kw: '医学图像 人工智能' },
  { label: '论文润色', kw: '论文润色 期刊发表' },
  { label: 'SCI 写作', kw: 'SCI论文 写作指导' },
]

const multiStyle = computed(() => versionCount.value > 1)
const useLlm = computed(() => !!llmProvider.value)

onMounted(async () => {
  try {
    await app.refreshLlm()
    if (app.llmConfig.has_key && app.llmConfig.provider) {
      llmProvider.value = app.llmConfig.provider
    }
  } catch {
    /* ignore */
  }
})

watch(
  () => app.llmConfig.has_key,
  (has) => {
    if (has && app.llmConfig.provider && !llmProvider.value) {
      llmProvider.value = app.llmConfig.provider
    }
  },
)

const canSend = computed(
  () =>
    (chat.keywords.length > 0 || input.value.trim().length > 0) && !generating.value,
)

function flushInput() {
  const raw = input.value.trim()
  if (!raw) return
  addKeywords(raw)
  input.value = ''
}

function addKeywords(raw: string) {
  raw.split(/\s+/).filter(Boolean).forEach((w) => {
    if (!chat.keywords.includes(w)) chat.keywords.push(w)
  })
}

function removeKw(i: number) {
  chat.keywords.splice(i, 1)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    flushInput()
    if (chat.keywords.length) generate()
  }
  if (e.key === 'Backspace' && !input.value && chat.keywords.length) {
    chat.keywords.pop()
  }
}

function quick(kw: string) {
  addKeywords(kw)
  generate()
}

async function generate() {
  flushInput()
  if (!chat.keywords.length || generating.value) return
  if (useLlm.value && !app.llmConfig.has_key) {
    toast('请先在设置中配置 LLM API Key')
    router.push({ name: 'settings-llm' })
    return
  }

  const kws = [...chat.keywords]
  const msgId = `u-${Date.now()}`
  chat.messages.push({ id: msgId, role: 'user', keywords: kws })
  const loadId = `a-${Date.now()}`
  chat.messages.push({
    id: loadId,
    role: 'assistant',
    keywords: kws,
    variants: [],
    safe: true,
    loading: true,
  })
  generating.value = true
  chat.keywords = []

  try {
    const data = await apiPost<GenerateResult>('/api/generate', {
      keywords: kws,
      version_count: versionCount.value,
      multi_style: multiStyle.value,
      ...(multiStyle.value ? {} : { style: style.value }),
      use_llm: useLlm.value,
      llm: llmProvider.value ? { provider: llmProvider.value } : {},
    })
    const safe = data.violations_check?.safe !== false
    const idx = chat.messages.findIndex((m) => m.id === loadId)
    if (idx >= 0) {
      chat.messages[idx] = {
        id: loadId,
        role: 'assistant',
        keywords: kws,
        variants: data.variants,
        safe,
      }
    }
    chat.lastVariants = data.variants
    if (data.history_id) chat.activeHistoryId = data.history_id
    await app.refreshStats()
    if (useLlm.value && !data.llm_used) {
      toast('AI 未生效，已回退为模板生成')
    }
  } catch (e) {
    chat.messages = chat.messages.filter((m) => m.id !== loadId)
    toast('生成失败: ' + (e as Error).message)
  } finally {
    generating.value = false
  }
}

function dismissBanner() {
  chat.historyBanner = null
  chat.activeHistoryId = null
}

function regenFromBanner() {
  if (!chat.historyBanner) return
  chat.keywords = [...chat.historyBanner.keywords]
  chat.historyBanner = null
  generate()
}
</script>

<template>
  <div class="chat-page">
    <div v-if="chat.historyBanner" class="banner">
      <div>
        <strong>{{ chat.historyBanner.keywords.join(' ') }}</strong>
        <span class="muted">
          {{ fmtDate(chat.historyBanner.created_at) }} ·
          {{ chat.historyBanner.variants.length }} 个版本
        </span>
      </div>
      <div class="banner-actions">
        <UiButton size="sm" @click="regenFromBanner">相同关键词再生成</UiButton>
        <UiButton size="sm" @click="compareOpen = true">版本对比</UiButton>
        <UiButton size="sm" variant="ghost" @click="dismissBanner">关闭</UiButton>
      </div>
    </div>

    <div class="chat-scroll">
      <div v-if="!chat.messages.length" class="welcome">
        <div class="welcome-icon">
          <AppIcon name="sparkles" :size="32" />
        </div>
        <h2>闲鱼学术辅导文案</h2>
        <p class="muted">
          推荐开启「AI 生成」：结合人设、服务范围与关键词撰写，并自动合规检测。
          版本数选 3 可一次得到标准 / 简洁 / 案例三种风格。
        </p>
        <p v-if="!app.llmConfig.has_key" class="muted warn-hint">
          尚未配置 API Key →
          <router-link :to="{ name: 'settings-llm' }">前往 LLM 设置</router-link>
        </p>
        <div class="chips">
          <button
            v-for="q in QUICK"
            :key="q.kw"
            type="button"
            class="chip"
            @click="quick(q.kw)"
          >
            {{ q.label }}
          </button>
        </div>
      </div>

      <template v-for="msg in chat.messages" :key="msg.id">
        <div v-if="msg.role === 'user'" class="msg user">
          <p>{{ msg.keywords.join(' · ') }}</p>
        </div>
        <div v-else class="msg assistant">
          <div v-if="msg.loading" class="msg-loading">
            <div class="msg-loading-dots" aria-hidden="true">
              <span /><span /><span />
            </div>
            <span>{{ useLlm ? 'AI 正在撰写文案…' : '正在生成文案…' }}</span>
          </div>
          <template v-else>
            <VariantCard
              v-for="(v, i) in msg.variants"
              :key="i"
              :variant="v"
              :index="i"
              :keywords="msg.keywords"
              :safe="msg.safe"
            />
          </template>
        </div>
      </template>
    </div>

    <footer class="composer">
      <div class="composer-box">
        <span v-for="(k, i) in chat.keywords" :key="k" class="kw-tag">
          {{ k }}<button type="button" @click="removeKw(i)">×</button>
        </span>
        <input
          v-model="input"
          type="text"
          placeholder="输入关键词，空格分隔，Enter 生成"
          autocomplete="off"
          @keydown="onKeydown"
        />
      </div>
      <div class="composer-bar">
        <label v-if="!multiStyle">风格
          <select v-model="style">
            <option value="comprehensive">标准版</option>
            <option value="concise_casual">简洁版</option>
            <option value="case_led">案例版</option>
          </select>
        </label>
        <span v-else class="muted style-hint">三风格套装</span>
        <label>版本
          <select v-model.number="versionCount">
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="3">3</option>
          </select>
        </label>
        <label>模式
          <select v-model="llmProvider">
            <option value="">仅模板</option>
            <option value="deepseek">AI · DeepSeek</option>
            <option value="qwen">AI · 通义千问</option>
            <option value="openai">AI · OpenAI</option>
          </select>
        </label>
        <UiButton
          variant="primary"
          class="send-btn"
          :disabled="!canSend"
          :loading="generating"
          title="生成文案 (Enter)"
          @click="generate"
        >
          <AppIcon name="arrow" :size="18" />
          生成
        </UiButton>
      </div>
    </footer>

    <CompareModal
      :open="compareOpen"
      :variants="chat.lastVariants"
      @close="compareOpen = false"
    />
  </div>
</template>

<style scoped>
.warn-hint {
  margin-top: 0.5rem;
}
.style-hint {
  font-size: 0.85rem;
  align-self: center;
}
.welcome-icon {
  color: var(--accent);
  background: var(--accent-soft);
}
.send-btn {
  margin-left: auto;
  border-radius: 999px !important;
  padding-left: 22px !important;
  padding-right: 22px !important;
}
.send-btn :deep(svg) {
  transform: rotate(-90deg);
}
</style>