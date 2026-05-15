<script setup lang="ts">
import type { Variant } from '@/types/api'
import { styleLabel, copyVariant } from '@/utils/format'
import { useToast } from '@/composables/useToast'

defineProps<{ open: boolean; variants: Variant[] }>()
const emit = defineEmits<{ close: [] }>()
const { toast } = useToast()

async function copy(v: Variant) {
  try {
    await copyVariant(v)
    toast('已复制')
  } catch {
    toast('复制失败')
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="modal-backdrop" @click.self="emit('close')">
      <div class="modal wide">
        <header class="modal-head">
          <h3>版本对比</h3>
          <button type="button" class="btn" @click="emit('close')">关闭</button>
        </header>
        <div class="compare-grid">
          <article v-for="(v, i) in variants" :key="i" class="compare-col">
            <h4>版本 {{ i + 1 }} · {{ styleLabel(v.style) }}</h4>
            <p class="compare-title">{{ v.title }}</p>
            <pre class="compare-body">{{ v.body }}</pre>
            <button type="button" class="btn sm primary" @click="copy(v)">复制此版</button>
          </article>
        </div>
      </div>
    </div>
  </Teleport>
</template>
