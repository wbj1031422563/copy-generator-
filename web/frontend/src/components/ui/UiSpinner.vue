<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 20 })
</script>

<template>
  <span
    class="ui-spinner"
    :style="{ width: size + 'px', height: size + 'px' }"
    role="status"
    aria-label="加载中"
  />
</template>

<style scoped>
.ui-spinner {
  display: inline-block;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
  opacity: 0.85;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
