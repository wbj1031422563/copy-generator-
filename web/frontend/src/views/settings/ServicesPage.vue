<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPut } from '@/api/client'
import { useToast } from '@/composables/useToast'
import { arrToLines, linesToArr } from '@/utils/form'

const { toast } = useToast()

const serviceTypes = ref('')
const levels = ref('')
const conferences = ref('')
const crossFields = ref('')
const defaultTags = ref('')
const servicesJson = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const s = await apiGet<Record<string, unknown>>('/api/services')
    serviceTypes.value = arrToLines(s.service_types as string[])
    levels.value = arrToLines(s.levels as string[])
    conferences.value = arrToLines(s.featured_conferences as string[])
    crossFields.value = arrToLines(s.cross_fields as string[])
    defaultTags.value = arrToLines(s.default_tags as string[])
    servicesJson.value = JSON.stringify(s, null, 2)
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
})

async function save() {
  try {
    let data: Record<string, unknown> = {}
    try {
      data = JSON.parse(servicesJson.value)
    } catch {
      toast('JSON 格式错误，请检查 domains 等复杂字段')
      return
    }
    data.service_types = linesToArr(serviceTypes.value)
    data.levels = linesToArr(levels.value)
    data.featured_conferences = linesToArr(conferences.value)
    data.cross_fields = linesToArr(crossFields.value)
    data.default_tags = linesToArr(defaultTags.value)
    await apiPut('/api/services', data)
    servicesJson.value = JSON.stringify(data, null, 2)
    toast('服务项目已保存')
  } catch (e) {
    toast('保存失败: ' + (e as Error).message)
  }
}
</script>

<template>
  <section class="card">
    <h3>服务项目</h3>
    <p class="muted">列表字段每行一条；研究方向 domains 请在下方 JSON 中维护。</p>
    <p v-if="loading" class="muted">加载中…</p>
    <template v-else>
      <label class="field">
        <span>服务类型</span>
        <textarea v-model="serviceTypes" class="input" rows="5" />
      </label>
      <label class="field">
        <span>期刊 / 会议级别</span>
        <textarea v-model="levels" class="input" rows="5" />
      </label>
      <label class="field">
        <span>代表会议</span>
        <textarea v-model="conferences" class="input" rows="4" />
      </label>
      <label class="field">
        <span>交叉方向</span>
        <textarea v-model="crossFields" class="input" rows="3" />
      </label>
      <label class="field">
        <span>默认闲鱼标签</span>
        <textarea v-model="defaultTags" class="input" rows="3" />
      </label>
      <label class="field">
        <span>完整 JSON（含 domains）</span>
        <textarea v-model="servicesJson" class="input mono" rows="12" />
      </label>
      <button type="button" class="btn primary" @click="save">保存服务</button>
    </template>
  </section>
</template>
