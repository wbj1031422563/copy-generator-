<script setup lang="ts">
import { ref } from 'vue'
import { apiPost } from '@/api/client'
import type { Variant } from '@/types/api'
import { styleLabel, copyVariant, copyText } from '@/utils/format'
import { useToast } from '@/composables/useToast'
import UiButton from '@/components/ui/UiButton.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

function sourceLabel(s: string) {
  if (s === 'llm') return 'AI'
  if (s === 'llm+template') return 'AI+模板'
  return '模板'
}

const props = defineProps<{
  variant: Variant
  index: number
  keywords?: string[]
  safe?: boolean
}>()

const { toast } = useToast()
const favorited = ref(false)

async function saveAsGood() {
  if (favorited.value) return
  try {
    await apiPost('/api/good-copies', {
      keywords: props.keywords || [],
      title: props.variant.title,
      body: props.variant.body,
      style: props.variant.style || '',
    })
    favorited.value = true
    toast('已收藏为优质范例，后续 AI 生成会参考此文风')
  } catch (e) {
    toast((e as Error).message)
  }
}

async function doCopy(mode: 'all' | 'title' | 'body' | 'tags') {
  try {
    const v = props.variant
    if (mode === 'all') await copyVariant(v)
    else if (mode === 'title') await copyText(v.title)
    else if (mode === 'body') await copyText(v.body)
    else if (v.tags?.length) await copyText(v.tags.join(' '))
    else return toast('暂无标签')
    toast(mode === 'all' ? '已复制标题+正文+标签' : '已复制')
  } catch {
    toast('复制失败，请允许剪贴板权限')
  }
}
</script>

<template>
  <article class="variant-card">
    <div class="variant-head">
      <span class="label">版本 {{ index + 1 }} · {{ styleLabel(variant.style) }}</span>
      <span v-if="variant.source" class="badge muted">{{ sourceLabel(variant.source) }}</span>
      <span v-if="safe !== undefined" class="badge" :class="safe ? 'ok' : 'warn'">
        {{ safe ? '合规' : '违禁' }}
      </span>
    </div>
    <h4 class="v-title">{{ variant.title }}</h4>
    <p class="title-len muted">{{ variant.title.length }} / 30 字</p>
    <p v-if="variant.tags?.length" class="tag-row">
      <span v-for="t in variant.tags" :key="t" class="tag-pill">{{ t }}</span>
    </p>
    <pre class="body">{{ variant.body }}</pre>
    <p class="body-len muted">{{ variant.body.length }} 字</p>
    <div class="variant-actions">
      <UiButton size="sm" variant="primary" @click="doCopy('all')">
        <AppIcon name="copy" :size="14" />
        复制全部
      </UiButton>
      <UiButton size="sm" @click="doCopy('title')">仅标题</UiButton>
      <UiButton size="sm" @click="doCopy('body')">仅正文</UiButton>
      <UiButton v-if="variant.tags?.length" size="sm" @click="doCopy('tags')">
        仅标签
      </UiButton>
      <UiButton
        size="sm"
        :variant="favorited ? 'primary' : 'secondary'"
        :disabled="favorited"
        title="加入优质范例库，提升后续 AI 生成质量"
        @click="saveAsGood"
      >
        <AppIcon name="star" :size="14" />
        {{ favorited ? '已收藏' : '收藏范例' }}
      </UiButton>
    </div>
  </article>
</template>
