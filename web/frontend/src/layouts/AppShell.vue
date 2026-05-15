<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NAV_GROUPS, SETTINGS_NAV, isSettingsRoute } from '@/config/navigation'
import { useAppStore, useChatStore } from '@/stores/app'
import { apiGet } from '@/api/client'
import { fetchAuthStatus, logout } from '@/api/auth'
import type { HistoryItem } from '@/types/api'
import { useToast } from '@/composables/useToast'
import AppIcon from '@/components/ui/AppIcon.vue'
import UiButton from '@/components/ui/UiButton.vue'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const chat = useChatStore()
const { toast } = useToast()

const recent = ref<HistoryItem[]>([])
const settingsOpen = ref(false)
const authEnabled = ref(false)
const authUser = ref<string | null>(null)

const pageTitle = computed(() => (route.meta.title as string) || '')
const inSettings = computed(() => isSettingsRoute(route.name))

const breadcrumb = computed(() => {
  const group = route.meta.group as string | undefined
  const title = route.meta.title as string | undefined
  if (!group || group === title) return ''
  return `${group} · ${title}`
})

function isActive(name: string) {
  return route.name === name
}

async function loadRecent() {
  try {
    recent.value = await apiGet<HistoryItem[]>('/api/history?limit=5')
  } catch {
    recent.value = []
  }
}

function go(name: string) {
  router.push({ name }).catch(() => {})
  app.sidebarOpen = false
  if (name.startsWith('settings-')) settingsOpen.value = true
}

function newChat() {
  chat.clearChat()
  router.push({ name: 'chat' }).catch(() => {})
  app.sidebarOpen = false
}

async function doLogout() {
  try {
    await logout()
  } catch {
    /* ignore */
  }
  authEnabled.value = false
  authUser.value = null
  await router.push({ name: 'login' })
}

async function openRecent(id: number) {
  try {
    const item = await apiGet<HistoryItem>(`/api/history/${id}`)
    chat.keywords = [...item.keywords]
    chat.activeHistoryId = item.id
    chat.historyBanner = item
    chat.lastVariants = JSON.parse(JSON.stringify(item.variants))
    chat.messages = [
      { id: 'u-h', role: 'user', keywords: item.keywords },
      {
        id: 'a-h',
        role: 'assistant',
        keywords: item.keywords,
        variants: item.variants,
        safe: item.meta?.violations_check?.safe !== false,
      },
    ]
    router.push({ name: 'chat' }).catch(() => {})
    app.sidebarOpen = false
  } catch (e) {
    toast((e as Error).message)
  }
}

onMounted(async () => {
  try {
    const s = await fetchAuthStatus()
    authEnabled.value = s.enabled
    authUser.value = s.username
  } catch {
    authEnabled.value = false
  }
  await Promise.all([
    app.refreshLlm().catch(() => {}),
    app.refreshStats().catch(() => {}),
    loadRecent(),
  ])
  settingsOpen.value = inSettings.value
})

watch(
  () => route.name,
  () => {
    loadRecent()
    if (inSettings.value) settingsOpen.value = true
  },
)
</script>

<template>
  <div class="app">
    <div
      class="backdrop"
      :class="{ show: app.sidebarOpen }"
      aria-hidden="true"
      @click="app.sidebarOpen = false"
    />

    <aside class="sidebar" :class="{ open: app.sidebarOpen }">
      <button type="button" class="brand" @click="go('dashboard')">
        <span class="brand-mark" aria-hidden="true">鱼</span>
        <span class="brand-text">
          <strong>闲鱼文案工坊</strong>
          <small>学术辅导 · 智能出稿</small>
        </span>
      </button>

      <UiButton variant="primary" block class="sidebar-new" @click="newChat">
        <AppIcon name="plus" :size="16" />
        新对话
      </UiButton>

      <div class="stats">
        <div class="stat">
          <b>{{ app.stats.total }}</b><span>生成</span>
        </div>
        <div class="stat">
          <b>{{ app.stats.templates }}</b><span>模板</span>
        </div>
      </div>

      <nav class="nav" aria-label="主导航">
        <template v-for="g in NAV_GROUPS" :key="g.id">
          <p class="nav-label">{{ g.label }}</p>
          <button
            v-for="item in g.items"
            :key="item.name"
            type="button"
            class="nav-item"
            :class="{ active: isActive(item.name) }"
            @click="go(item.name)"
          >
            <span class="nav-icon"><AppIcon :name="item.icon" :size="18" /></span>
            {{ item.label }}
          </button>
        </template>

        <p class="nav-label">系统设置</p>
        <button
          type="button"
          class="nav-item nav-item-parent"
          :class="{ active: inSettings, open: settingsOpen }"
          @click="settingsOpen = !settingsOpen"
        >
          <span class="nav-icon"><AppIcon name="settings" :size="18" /></span>
          系统配置
          <span class="nav-chevron" aria-hidden="true">{{ settingsOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-show="settingsOpen" class="nav-sub">
          <button
            v-for="item in SETTINGS_NAV"
            :key="item.name"
            type="button"
            class="nav-item sub"
            :class="{ active: isActive(item.name) }"
            @click="go(item.name)"
          >
            <span class="nav-icon sm"><AppIcon :name="item.icon" :size="16" /></span>
            {{ item.label }}
          </button>
        </div>
      </nav>

      <div class="recent">
        <p class="nav-label">最近生成</p>
        <p v-if="!recent.length" class="muted small">暂无记录</p>
        <button
          v-for="item in recent"
          :key="item.id"
          type="button"
          class="recent-item"
          @click="openRecent(item.id)"
        >
          {{ (item.keywords || []).slice(0, 2).join(' ') }}
        </button>
        <button type="button" class="link-btn light" @click="go('history')">
          查看全部 →
        </button>
      </div>

      <div class="sidebar-foot">
        <span class="ver">v2.2</span>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <button
          type="button"
          class="icon-btn"
          aria-label="打开菜单"
          @click="app.sidebarOpen = true"
        >
          <AppIcon name="menu" :size="20" />
        </button>
        <div class="topbar-titles">
          <h1>{{ pageTitle }}</h1>
          <p v-if="breadcrumb" class="breadcrumb">{{ breadcrumb }}</p>
        </div>
        <button
          type="button"
          class="llm-pill"
          :class="app.llmConfig.has_key ? 'ok' : 'warn'"
          @click="go('settings-llm')"
        >
          <span class="llm-dot" :class="app.llmConfig.has_key ? 'ok' : 'warn'" />
          {{ app.llmConfig.has_key ? `LLM · ${app.llmConfig.provider}` : '配置 LLM' }}
        </button>
        <button
          v-if="authEnabled"
          type="button"
          class="logout-btn"
          title="退出登录"
          @click="doLogout"
        >
          退出
        </button>
      </header>
      <div class="main-body" :class="{ 'main-body-chat': route.name === 'chat' }">
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style scoped>
.sidebar-new {
  margin-bottom: 4px;
}
.llm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
  vertical-align: middle;
}
.llm-dot.ok {
  background: var(--ok);
  box-shadow: 0 0 6px rgba(0, 181, 120, 0.5);
}
.llm-dot.warn {
  background: var(--warn);
}
.nav-chevron {
  margin-left: auto;
  opacity: 0.45;
  transform: rotate(90deg);
}
.nav-item-parent.open .nav-chevron {
  transform: rotate(-90deg);
}
.logout-btn {
  margin-left: 8px;
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
}
.logout-btn:hover {
  color: var(--text);
  border-color: var(--accent);
}
</style>
