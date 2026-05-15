<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{
  label: string
  value: string | number
  icon?: string
  tone?: 'default' | 'ok' | 'warn' | 'accent'
}>()
</script>

<template>
  <div class="ui-stat" :class="tone || 'default'">
    <div v-if="icon" class="ui-stat-icon">
      <AppIcon :name="icon" :size="20" />
    </div>
    <div class="ui-stat-body">
      <b>{{ value }}</b>
      <span>{{ label }}</span>
    </div>
  </div>
</template>

<style scoped>
.ui-stat {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.ui-stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper-2);
  color: var(--muted);
  flex-shrink: 0;
}
.ui-stat-body b {
  display: block;
  font-size: 24px;
  font-family: var(--font-display);
  line-height: 1.2;
  margin-bottom: 2px;
}
.ui-stat-body span {
  font-size: 12px;
  color: var(--muted);
}
.ui-stat.accent .ui-stat-icon {
  background: var(--accent-soft);
  color: var(--accent);
}
.ui-stat.accent b {
  color: var(--accent);
}
.ui-stat.ok {
  border-color: #86efac;
  background: linear-gradient(135deg, #f0fdf4 0%, #fff 100%);
}
.ui-stat.ok .ui-stat-icon {
  background: var(--teal-soft);
  color: var(--ok);
}
.ui-stat.warn {
  border-color: #fcd34d;
  background: linear-gradient(135deg, #fffbeb 0%, #fff 100%);
}
.ui-stat.warn .ui-stat-icon {
  background: #fef3c7;
  color: var(--warn);
}
</style>
