<script setup lang="ts">
import UiSpinner from './UiSpinner.vue'

withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
    size?: 'sm' | 'md' | 'lg'
    loading?: boolean
    disabled?: boolean
    block?: boolean
    type?: 'button' | 'submit'
  }>(),
  {
    variant: 'secondary',
    size: 'md',
    loading: false,
    disabled: false,
    block: false,
    type: 'button',
  },
)
</script>

<template>
  <button
    :type="type"
    class="ui-btn"
    :class="[variant, size, { block, loading }]"
    :disabled="disabled || loading"
  >
    <UiSpinner v-if="loading" class="ui-btn-spinner" :size="16" />
    <slot />
  </button>
</template>

<style scoped>
.ui-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink);
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s,
    border-color 0.15s,
    transform 0.12s,
    box-shadow 0.15s;
  user-select: none;
}
.ui-btn:hover:not(:disabled) {
  background: var(--paper);
  border-color: #d4d4d8;
}
.ui-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.ui-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
.ui-btn.md {
  padding: 10px 18px;
  font-size: 14px;
}
.ui-btn.sm {
  padding: 7px 14px;
  font-size: 13px;
}
.ui-btn.lg {
  padding: 12px 22px;
  font-size: 15px;
}
.ui-btn.primary {
  background: linear-gradient(135deg, var(--accent) 0%, #ff8533 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 4px 14px var(--accent-glow);
}
.ui-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--accent-hover) 0%, #ff7a26 100%);
  border-color: transparent;
}
.ui-btn.ghost {
  background: transparent;
  border-color: transparent;
}
.ui-btn.ghost:hover:not(:disabled) {
  background: var(--paper-2);
}
.ui-btn.danger {
  color: var(--danger);
  border-color: #fecaca;
  background: #fef2f2;
}
.ui-btn.block {
  width: 100%;
}
.ui-btn-spinner {
  color: currentColor;
}
</style>
