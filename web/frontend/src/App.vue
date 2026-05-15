<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'
import ToastHost from '@/components/ToastHost.vue'
import ApiHealthBanner from '@/components/system/ApiHealthBanner.vue'

const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
</script>

<template>
  <div class="app-root">
    <template v-if="isLoginPage">
      <RouterView />
    </template>
    <template v-else>
      <ApiHealthBanner />
      <AppShell />
    </template>
    <ToastHost />
  </div>
</template>

<style>
.app-root {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.app-root .app {
  flex: 1;
  min-height: 0;
}
</style>
