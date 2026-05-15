<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPut } from '@/api/client'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()

const versionCount = ref(3)
const tone = ref('')
const maxTitle = ref(30)
const maxBody = ref(500)
const loading = ref(true)

onMounted(async () => {
  try {
    const st = await apiGet<{
      version_count?: number
      tone?: string
      max_title_len?: number
      max_body_len?: number
    }>('/api/style')
    versionCount.value = st.version_count ?? 3
    tone.value = st.tone || ''
    maxTitle.value = st.max_title_len ?? 30
    maxBody.value = st.max_body_len ?? 500
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
})

async function save() {
  try {
    const base = await apiGet<Record<string, unknown>>('/api/style')
    await apiPut('/api/style', {
      ...base,
      version_count: versionCount.value,
      tone: tone.value,
      max_title_len: maxTitle.value,
      max_body_len: maxBody.value,
    })
    toast('生成风格已保存')
  } catch (e) {
    toast('保存失败: ' + (e as Error).message)
  }
}
</script>

<template>
  <section class="card">
    <h3>生成风格</h3>
    <p class="muted">控制默认版本数与字数上限；多版本对话生成时使用 style.json 中的三套预设风格。</p>
    <p v-if="loading" class="muted">加载中…</p>
    <template v-else>
      <label class="field">
        <span>默认版本数</span>
        <select v-model.number="versionCount" class="input">
          <option :value="1">1</option>
          <option :value="2">2</option>
          <option :value="3">3</option>
        </select>
      </label>
      <label class="field">
        <span>语气描述</span>
        <input v-model="tone" class="input" />
      </label>
      <label class="field row2">
        <span>标题最大字数</span>
        <input v-model.number="maxTitle" type="number" class="input" />
        <span>正文最大字数</span>
        <input v-model.number="maxBody" type="number" class="input" />
      </label>
      <button type="button" class="btn primary" @click="save">保存风格</button>
    </template>
  </section>
</template>
