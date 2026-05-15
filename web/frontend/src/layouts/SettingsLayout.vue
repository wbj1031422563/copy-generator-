<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { SETTINGS_NAV } from '@/config/navigation'
import AppIcon from '@/components/ui/AppIcon.vue'
const route = useRoute()
const router = useRouter()

const current = computed(() =>
  SETTINGS_NAV.find((item) => item.name === route.name),
)

function go(name: string) {
  router.push({ name })
}
</script>

<template>
  <div class="page wide settings-layout">
    <div class="settings-shell">
      <aside class="settings-nav card">
        <p class="nav-label">配置项</p>
        <button
          v-for="item in SETTINGS_NAV"
          :key="item.name"
          type="button"
          class="settings-nav-item"
          :class="{ active: route.name === item.name }"
          @click="go(item.name)"
        >
          <span class="settings-nav-icon"><AppIcon :name="item.icon" :size="18" /></span>
          <span class="settings-nav-text">
            <strong>{{ item.label }}</strong>
            <small>{{ item.description }}</small>
          </span>
        </button>
      </aside>

      <div class="settings-content">
        <p v-if="current" class="settings-breadcrumb muted">
          系统设置 / {{ current.label }}
        </p>
        <RouterView />
      </div>
    </div>
  </div>
</template>
