<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPut } from '@/api/client'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()
const wordsJson = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const w = await apiGet<Record<string, unknown>>('/api/sensitive-words')
    wordsJson.value = JSON.stringify(w, null, 2)
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
})

async function save() {
  try {
    const data = JSON.parse(wordsJson.value)
    await apiPut('/api/sensitive-words', data)
    toast('敏感词库已保存')
  } catch {
    toast('保存失败，请检查 JSON 格式')
  }
}
</script>

<template>
  <section class="card">
    <h3>敏感词库</h3>
    <p class="muted">
      direct_replace / must_avoid 等字段，保存后立即生效于生成与合规检测。
    </p>
    <p v-if="loading" class="muted">加载中…</p>
    <template v-else>
      <textarea v-model="wordsJson" class="input mono" rows="20" />
      <div class="row mt">
        <button type="button" class="btn primary" @click="save">保存词库</button>
        <RouterLink :to="{ name: 'checker' }" class="btn">去合规检测 →</RouterLink>
      </div>
    </template>
  </section>
</template>
