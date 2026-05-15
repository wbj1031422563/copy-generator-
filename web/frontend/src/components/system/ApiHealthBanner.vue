<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet } from '@/api/client'
import UiButton from '@/components/ui/UiButton.vue'

const ok = ref(true)
const detail = ref('')
const checking = ref(true)

async function check() {
  checking.value = true
  try {
    const data = await apiGet<{ status: string; frontend?: string }>('/api/health')
    ok.value = data.status === 'up'
    detail.value = data.frontend === 'missing_build' ? '前端构建缺失' : ''
  } catch (e) {
    ok.value = false
    detail.value = (e as Error).message || '无法连接后端'
  } finally {
    checking.value = false
  }
}

onMounted(check)
</script>

<template>
  <div v-if="!checking && !ok" class="api-banner" role="alert">
    <div>
      <strong>后端未连接</strong>
      <p>请确认已运行 start.bat 或 uvicorn，地址为 http://127.0.0.1:8765</p>
      <p v-if="detail" class="muted small">{{ detail }}</p>
    </div>
    <UiButton size="sm" variant="primary" @click="check">重试</UiButton>
  </div>
</template>

<style scoped>
.api-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 20px;
  background: #fef2f2;
  border-bottom: 1px solid #fecaca;
  color: #991b1b;
  flex-shrink: 0;
}
.api-banner strong {
  display: block;
  margin-bottom: 2px;
}
.api-banner p {
  font-size: 13px;
  margin: 0;
}
</style>
