<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
}>()
</script>

<template>
  <section class="ui-card">
    <header v-if="title || $slots.header || $slots.actions" class="ui-card-head">
      <div class="ui-card-head-text">
        <slot name="header">
          <h3 v-if="title">{{ title }}</h3>
          <p v-if="subtitle" class="muted">{{ subtitle }}</p>
        </slot>
      </div>
      <div v-if="$slots.actions" class="ui-card-actions">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </section>
</template>

<style scoped>
.ui-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}
.ui-card-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.ui-card-head h3 {
  font-size: 17px;
  margin-bottom: 4px;
}
.ui-card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
