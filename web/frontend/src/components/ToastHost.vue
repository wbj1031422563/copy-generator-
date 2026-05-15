<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { message, visible } = useToast()
</script>

<template>
  <Transition name="toast">
    <div v-if="visible" class="toast" role="status">{{ message }}</div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  padding: 14px 24px;
  background: var(--ink);
  color: #fff;
  border: 1px solid rgba(255, 104, 0, 0.4);
  min-width: 200px;
  text-align: center;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}
</style>
