<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiPostRaw, apiPut } from '@/api/client'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'

const app = useAppStore()
const { toast } = useToast()

const provider = ref('deepseek')
const baseUrl = ref('')
const model = ref('')
const apiKey = ref('')
const keyHint = ref('')

onMounted(async () => {
  await app.refreshLlm()
  provider.value = app.llmConfig.provider || 'deepseek'
  baseUrl.value = app.llmConfig.base_url || ''
  model.value = app.llmConfig.model || ''
  keyHint.value = app.llmConfig.has_key
    ? `当前: ${app.llmConfig.key_hint}`
    : '未配置 API Key'
})

async function save() {
  try {
    const body: Record<string, string> = {
      provider: provider.value,
      base_url: baseUrl.value.trim(),
      model: model.value.trim(),
    }
    if (apiKey.value.trim()) body.api_key = apiKey.value.trim()
    else body.api_key = '__KEEP__'
    await apiPut('/api/llm-config', body)
    apiKey.value = ''
    await app.refreshLlm()
    keyHint.value = app.llmConfig.has_key
      ? `当前: ${app.llmConfig.key_hint}`
      : '未配置 API Key'
    toast('LLM 配置已保存')
  } catch (e) {
    toast((e as Error).message)
  }
}

async function testConn() {
  try {
    const body: Record<string, string> = {
      provider: provider.value,
      base_url: baseUrl.value.trim(),
      model: model.value.trim(),
    }
    if (apiKey.value.trim()) body.api_key = apiKey.value.trim()
    else body.api_key = '__KEEP__'
    const r = await apiPostRaw<{ ok: boolean; data: { reply: string } }>(
      '/api/llm-config/test',
      body,
    )
    toast('连接成功: ' + (r.data?.reply || 'OK'))
  } catch (e) {
    toast('测试失败: ' + (e as Error).message)
  }
}
</script>

<template>
  <section class="card">
    <h3>LLM 配置</h3>
    <p class="muted">支持 DeepSeek / 通义千问 / OpenAI 兼容接口，也可使用环境变量。</p>
    <label class="field">
      <span>提供商</span>
      <select v-model="provider" class="input">
        <option value="deepseek">DeepSeek</option>
        <option value="qwen">通义千问</option>
        <option value="openai">OpenAI</option>
      </select>
    </label>
    <label class="field">
      <span>API Key</span>
      <input v-model="apiKey" type="password" class="input" placeholder="留空则保持原 Key" />
      <small class="muted">{{ keyHint }}</small>
    </label>
    <label class="field">
      <span>Base URL（可选）</span>
      <input v-model="baseUrl" class="input" placeholder="默认使用官方地址" />
    </label>
    <label class="field">
      <span>模型（可选）</span>
      <input v-model="model" class="input" placeholder="默认 deepseek-chat 等" />
    </label>
    <div class="row">
      <button type="button" class="btn primary" @click="save">保存</button>
      <button type="button" class="btn" @click="testConn">测试连接</button>
    </div>
  </section>
</template>
