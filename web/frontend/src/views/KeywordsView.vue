<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiGet } from '@/api/client'
import type { KeywordDomain } from '@/types/api'
import { PRESET_KEY, type KwPreset, useChatStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const chat = useChatStore()
const { toast } = useToast()

const staging = ref<string[]>([])
const domains = ref<KeywordDomain[]>([])
const search = ref('')
const presetName = ref('')
const presets = ref<KwPreset[]>([])
const custom = ref('')

function loadPresets() {
  try {
    presets.value = JSON.parse(localStorage.getItem(PRESET_KEY) || '[]')
  } catch {
    presets.value = []
  }
}

function savePresets(list: KwPreset[]) {
  localStorage.setItem(PRESET_KEY, JSON.stringify(list))
  presets.value = list
}

function addStaging(w: string) {
  const t = w.trim()
  if (t && !staging.value.includes(t)) staging.value.push(t)
}

function removeStaging(i: number) {
  staging.value.splice(i, 1)
}

async function load() {
  const data = await apiGet<{ domains: KeywordDomain[] }>('/api/keywords')
  domains.value = data.domains || []
}

const filteredDomains = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return domains.value
  return domains.value
    .map((d) => ({
      ...d,
      keywords: (d.keywords || []).filter(
        (k) =>
          k.toLowerCase().includes(q) || (d.name || '').toLowerCase().includes(q),
      ),
    }))
    .filter((d) => d.keywords.length)
})

onMounted(() => {
  loadPresets()
  load().catch((e) => toast((e as Error).message))
})

function savePreset() {
  const name = presetName.value.trim()
  if (!name) return toast('请输入预设名称')
  if (!staging.value.length) return toast('请先添加关键词')
  const list = [...presets.value]
  const idx = list.findIndex((p) => p.name === name)
  const entry = { name, keywords: [...staging.value] }
  if (idx >= 0) list[idx] = entry
  else list.push(entry)
  savePresets(list)
  presetName.value = ''
  toast('预设已保存')
}

function toChat() {
  if (!staging.value.length) return toast('请先添加关键词')
  chat.keywords = [...staging.value]
  router.push({ name: 'chat' })
  toast('已填入对话，点击发送生成')
}
</script>

<template>
  <div class="page wide kw-page">
    <div class="kw-grid">
      <section class="card">
        <h3>领域词库</h3>
        <input v-model="search" type="search" placeholder="搜索关键词…" class="input" />
        <details
          v-for="d in filteredDomains"
          :key="d.name"
          class="domain"
          :open="!!search"
        >
          <summary>{{ d.name }} ({{ d.keywords.length }})</summary>
          <div class="chips">
            <button
              v-for="k in d.keywords"
              :key="k"
              type="button"
              class="chip sm"
              @click="addStaging(k)"
            >
              {{ k }}
            </button>
          </div>
        </details>
      </section>

      <section class="card">
        <h3>待生成列表</h3>
        <div class="staging">
          <p v-if="!staging.length" class="muted">从左侧点击添加</p>
          <span v-for="(k, i) in staging" :key="k" class="kw-tag">
            {{ k }}<button type="button" @click="removeStaging(i)">×</button>
          </span>
        </div>
        <input
          v-model="custom"
          class="input"
          placeholder="自定义关键词，Enter 添加"
          @keydown.enter.prevent="
            addStaging(custom);
            custom = '';
          "
        />
        <div class="row">
          <button type="button" class="btn primary" @click="toChat">填入对话</button>
          <button type="button" class="btn ghost" @click="staging = []">清空</button>
        </div>

        <h3 class="mt">我的预设</h3>
        <div class="row">
          <input v-model="presetName" class="input" placeholder="预设名称" />
          <button type="button" class="btn sm" @click="savePreset">保存</button>
        </div>
        <ul class="preset-list">
          <li v-for="(p, i) in presets" :key="p.name">
            <button type="button" class="link-btn" @click="staging = [...p.keywords]">
              {{ p.name }}
            </button>
            <button
              type="button"
              class="del"
              @click="
                savePresets(presets.filter((_, j) => j !== i))
              "
            >
              ×
            </button>
          </li>
        </ul>
        <p v-if="!presets.length" class="muted">暂无预设</p>
      </section>
    </div>
  </div>
</template>
