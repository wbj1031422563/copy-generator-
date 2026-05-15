<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, exportVariants, downloadText } from '@/api/client'
import type { HistoryItem } from '@/types/api'
import { useToast } from '@/composables/useToast'
import { fmtDate } from '@/utils/format'

const { toast } = useToast()
const items = ref<HistoryItem[]>([])
const selected = ref<Set<number>>(new Set())
const selectAll = ref(false)
const format = ref<'txt' | 'json'>('txt')

onMounted(async () => {
  try {
    items.value = await apiGet<HistoryItem[]>('/api/history?limit=200')
  } catch (e) {
    toast((e as Error).message)
  }
})

function toggle(id: number) {
  const s = new Set(selected.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selected.value = s
  selectAll.value = s.size === items.value.length && items.value.length > 0
}

function onSelectAll() {
  if (selectAll.value) {
    selected.value = new Set(items.value.map((i) => i.id))
  } else {
    selected.value = new Set()
  }
}

async function exportSelected() {
  const ids = [...selected.value]
  if (!ids.length) return toast('请勾选记录')
  const variants: Record<string, unknown>[] = []
  for (const id of ids) {
    try {
      const item = await apiGet<HistoryItem>(`/api/history/${id}`)
      item.variants.forEach((v, i) => {
        variants.push({
          ...v,
          version: `${item.keywords.join('_')}_v${i + 1}`,
        })
      })
    } catch {
      /* skip */
    }
  }
  const ext = format.value === 'json' ? 'json' : 'txt'
  const content = await exportVariants(variants, format.value)
  downloadText(
    content,
    `export-${Date.now()}.${ext}`,
    format.value === 'json' ? 'application/json' : 'text/plain',
  )
  toast('已下载')
}
</script>

<template>
  <div class="page">
    <section class="card">
      <div class="row head">
        <h3>导出历史文案</h3>
        <div class="row">
          <label>
            <input v-model="selectAll" type="checkbox" @change="onSelectAll" />
            全选
          </label>
          <select v-model="format">
            <option value="txt">TXT</option>
            <option value="json">JSON</option>
          </select>
          <button type="button" class="btn primary" @click="exportSelected">
            导出选中
          </button>
        </div>
      </div>
      <p v-if="!items.length" class="empty">暂无历史可导出</p>
      <label v-for="item in items" :key="item.id" class="export-row">
        <input
          type="checkbox"
          :checked="selected.has(item.id)"
          @change="toggle(item.id)"
        />
        <span>
          <strong>{{ item.keywords.join(' ') }}</strong>
          <span class="muted">
            {{ fmtDate(item.created_at) }} · {{ item.variant_count }} 版
          </span>
        </span>
      </label>
    </section>
  </div>
</template>
