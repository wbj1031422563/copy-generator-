import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { HistoryItem, LlmConfig, Variant } from '@/types/api'
import { apiGet } from '@/api/client'

export const useAppStore = defineStore('app', () => {
  const llmConfig = ref<LlmConfig>({
    provider: 'deepseek',
    base_url: '',
    model: '',
    has_key: false,
  })
  const stats = ref({ total: 0, templates: 0 })
  const sidebarOpen = ref(false)

  async function refreshLlm() {
    try {
      llmConfig.value = await apiGet<LlmConfig>('/api/llm-config')
    } catch {
      llmConfig.value = {
        provider: 'deepseek',
        base_url: '',
        model: '',
        has_key: false,
      }
    }
  }

  async function refreshStats() {
    try {
      const d = await apiGet<{
        total_generations: number
        template_count: number
      }>('/api/stats')
      stats.value = {
        total: d.total_generations ?? 0,
        templates: d.template_count ?? 0,
      }
    } catch {
      stats.value = { total: 0, templates: 0 }
    }
  }

  return {
    llmConfig,
    stats,
    sidebarOpen,
    refreshLlm,
    refreshStats,
  }
})

export const useChatStore = defineStore('chat', () => {
  const keywords = ref<string[]>([])
  const messages = ref<
    Array<
      | { id: string; role: 'user'; keywords: string[] }
      | {
          id: string
          role: 'assistant'
          keywords: string[]
          variants: Variant[]
          safe: boolean
          loading?: boolean
        }
    >
  >([])
  const activeHistoryId = ref<number | null>(null)
  const historyBanner = ref<HistoryItem | null>(null)
  const lastVariants = ref<Variant[]>([])

  function clearChat() {
    keywords.value = []
    messages.value = []
    activeHistoryId.value = null
    historyBanner.value = null
    lastVariants.value = []
  }

  return {
    keywords,
    messages,
    activeHistoryId,
    historyBanner,
    lastVariants,
    clearChat,
  }
})

export const PRESET_KEY = 'copygen_kw_presets'

export interface KwPreset {
  name: string
  keywords: string[]
}
