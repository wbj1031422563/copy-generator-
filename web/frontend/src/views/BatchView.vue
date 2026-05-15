<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiPost } from '@/api/client'
import type { BatchResultItem, StyleKey } from '@/types/api'
import { useAppStore, useChatStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'
import { copyVariant } from '@/utils/format'

const app = useAppStore()
const chat = useChatStore()
const router = useRouter()
const { toast } = useToast()

const lines = ref('')
const style = ref<StyleKey>('comprehensive')
const llm = ref('')
const running = ref(false)
const progress = ref(0)
const results = ref<BatchResultItem[]>([])

onMounted(async () => {
  try {
    await app.refreshLlm()
    if (app.llmConfig.has_key && app.llmConfig.provider) {
      llm.value = app.llmConfig.provider
    }
  } catch {
    /* ignore */
  }
})

async function run() {
  const sets = lines.value
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .map((l) => l.split(/\s+/).filter(Boolean))
  if (!sets.length) {
    toast('请至少输入一行关键词')
    return
  }
  if (llm.value && !app.llmConfig.has_key) {
    toast('请先配置 LLM API Key')
    router.push({ name: 'settings-llm' })
    return
  }

  running.value = true
  progress.value = 10
  results.value = []
  try {
    const data = await apiPost<{ results: BatchResultItem[] }>('/api/generate-batch', {
      keyword_sets: sets,
      style: style.value,
      use_llm: !!llm.value,
      llm: llm.value ? { provider: llm.value } : {},
    })
    progress.value = 100
    results.value = data.results
    await app.refreshStats()
    toast(`完成 ${data.results.length} 组`)
  } catch (e) {
    toast('批量失败: ' + (e as Error).message)
  } finally {
    running.value = false
  }
}

function toChat(item: BatchResultItem) {
  chat.keywords = [...item.keywords]
  router.push({ name: 'chat' }).catch(() => {})
  toast('已填入对话')
}

async function doCopy(v: { title: string; body: string; tags?: string[] }) {
  try {
    await copyVariant(v)
    toast('已复制')
  } catch {
    toast('复制失败')
  }
}
</script>

<template>
  <div class="page">
    <section class="card">
      <h3>批量生成</h3>
      <p class="muted">每行一组关键词，空格分隔多个词</p>
      <textarea v-model="lines" rows="8" placeholder="深度学习 论文辅导&#10;医学图像 分割&#10;..." />
      <div class="row">
        <label>风格
          <select v-model="style">
            <option value="comprehensive">标准版</option>
            <option value="concise_casual">简洁版</option>
            <option value="case_led">案例版</option>
          </select>
        </label>
        <label>模式
          <select v-model="llm">
            <option value="">仅模板</option>
            <option value="deepseek">AI · DeepSeek</option>
            <option value="qwen">AI · 通义千问</option>
            <option value="openai">AI · OpenAI</option>
          </select>
        </label>
        <button type="button" class="btn primary" :disabled="running" @click="run">
          {{ running ? '生成中…' : '开始批量' }}
        </button>
      </div>
      <div v-if="running || progress === 100" class="progress">
        <div class="fill" :style="{ width: progress + '%' }" />
      </div>
    </section>

    <section v-if="results.length" class="card results">
      <article v-for="(r, idx) in results" :key="idx" class="batch-item">
        <h4>
          #{{ idx + 1 }} · {{ r.keywords.join(' ') }}
          <span class="badge" :class="r.violations_check?.safe ? 'ok' : 'warn'">
            {{ r.violations_check?.safe ? '合规' : '违禁' }}
          </span>
        </h4>
        <p class="title">{{ r.variants[0]?.title }}</p>
        <pre class="body">{{ r.variants[0]?.body }}</pre>
        <div class="actions">
          <button type="button" class="btn sm primary" @click="doCopy(r.variants[0]!)">
            复制
          </button>
          <button type="button" class="btn sm" @click="toChat(r)">填入对话</button>
        </div>
      </article>
    </section>
  </div>
</template>
