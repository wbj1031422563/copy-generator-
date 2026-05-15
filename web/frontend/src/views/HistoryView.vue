<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiDelete, apiGet } from '@/api/client'
import type { HistoryItem } from '@/types/api'
import { useChatStore } from '@/stores/app'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'
import { fmtDate, copyVariant } from '@/utils/format'
import type { Variant } from '@/types/api'
import CompareModal from '@/components/CompareModal.vue'

const route = useRoute()
const router = useRouter()
const chat = useChatStore()
const app = useAppStore()
const { toast } = useToast()

const items = ref<HistoryItem[]>([])
const search = ref('')
const selectedId = ref<number | null>(null)
const detail = ref<HistoryItem | null>(null)
const compareOpen = ref(false)

async function load() {
  const q = search.value.trim()
  const path = q
    ? `/api/history?search=${encodeURIComponent(q)}&limit=200`
    : '/api/history?limit=200'
  items.value = await apiGet<HistoryItem[]>(path)
}

async function select(id: number) {
  selectedId.value = id
  detail.value = await apiGet<HistoryItem>(`/api/history/${id}`)
}

async function remove() {
  if (!detail.value || !confirm('删除此记录？')) return
  await apiDelete(`/api/history/${detail.value.id}`)
  selectedId.value = null
  detail.value = null
  await load()
  await app.refreshStats()
  toast('已删除')
}

async function clearAll() {
  if (!confirm('清空全部历史？')) return
  await apiDelete('/api/history')
  selectedId.value = null
  detail.value = null
  await load()
  await app.refreshStats()
  toast('已清空')
}

async function copyOne(v: Variant) {
  try {
    await copyVariant(v)
    toast('已复制')
  } catch {
    toast('复制失败')
  }
}

function openInChat() {
  if (!detail.value) return
  chat.clearChat()
  chat.keywords = [...detail.value.keywords]
  chat.activeHistoryId = detail.value.id
  chat.historyBanner = detail.value
  chat.lastVariants = JSON.parse(JSON.stringify(detail.value.variants))
  chat.messages = [
    { id: 'u', role: 'user', keywords: detail.value.keywords },
    {
      id: 'a',
      role: 'assistant',
      keywords: detail.value.keywords,
      variants: detail.value.variants,
      safe: detail.value.meta?.violations_check?.safe !== false,
    },
  ]
  router.push({ name: 'chat' })
}

let debounce: ReturnType<typeof setTimeout>
watch(search, () => {
  clearTimeout(debounce)
  debounce = setTimeout(load, 300)
})

onMounted(async () => {
  await load()
  const id = route.query.id
  if (id) await select(parseInt(String(id), 10))
})

watch(
  () => route.query.id,
  async (id) => {
    if (id) await select(parseInt(String(id), 10))
  },
)
</script>

<template>
  <div class="page wide history-page">
    <div class="history-layout">
      <aside class="card list-panel">
        <div class="row head">
          <h3>历史记录 ({{ items.length }})</h3>
          <button type="button" class="btn sm ghost" @click="clearAll">清空</button>
        </div>
        <input v-model="search" type="search" class="input" placeholder="搜索关键词…" />
        <p v-if="!items.length" class="empty">暂无记录</p>
        <button
          v-for="item in items"
          :key="item.id"
          type="button"
          class="history-row"
          :class="{ active: selectedId === item.id }"
          @click="select(item.id)"
        >
          <span class="title">{{ item.keywords.join(' ') }}</span>
          <span class="meta muted">
            {{ fmtDate(item.created_at) }} · {{ item.variant_count }} 版
            <span
              class="badge"
              :class="item.meta?.violations_check?.safe !== false ? 'ok' : 'warn'"
            >
              {{ item.meta?.violations_check?.safe !== false ? '合规' : '违禁' }}
            </span>
          </span>
        </button>
      </aside>

      <section class="card detail-panel">
        <p v-if="!detail" class="empty">选择左侧记录查看详情</p>
        <template v-else>
          <div class="detail-head">
            <h3>{{ detail.keywords.join(' ') }}</h3>
            <p class="muted">{{ fmtDate(detail.created_at) }} · {{ detail.style }}</p>
            <div class="row">
              <button type="button" class="btn sm primary" @click="openInChat">
                在对话中打开
              </button>
              <button type="button" class="btn sm" @click="compareOpen = true">
                版本对比
              </button>
              <button type="button" class="btn sm ghost" @click="remove">删除</button>
            </div>
          </div>
          <article
            v-for="(v, i) in detail.variants"
            :key="i"
            class="variant-card compact"
          >
            <div class="variant-head">
              <span>版本 {{ i + 1 }}</span>
              <span
                class="badge"
                :class="detail.meta?.violations_check?.safe !== false ? 'ok' : 'warn'"
              >
                {{ detail.meta?.violations_check?.safe !== false ? '合规' : '违禁' }}
              </span>
            </div>
            <h4>{{ v.title }}</h4>
            <pre>{{ v.body }}</pre>
            <button type="button" class="btn sm primary" @click="copyOne(v)">
              复制
            </button>
          </article>
        </template>
      </section>
    </div>

    <CompareModal
      :open="compareOpen"
      :variants="detail?.variants || []"
      @close="compareOpen = false"
    />
  </div>
</template>
