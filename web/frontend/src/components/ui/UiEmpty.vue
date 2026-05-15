<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{
  title?: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="ui-empty">
    <div class="ui-empty-icon">
      <AppIcon :name="icon || 'sparkles'" :size="28" />
    </div>
    <h4 v-if="title">{{ title }}</h4>
    <p v-if="description" class="muted">{{ description }}</p>
    <div v-if="$slots.default" class="ui-empty-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.ui-empty {
  text-align: center;
  padding: 40px 24px;
}
.ui-empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 16px;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ui-empty h4 {
  font-size: 16px;
  margin-bottom: 6px;
}
.ui-empty-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
