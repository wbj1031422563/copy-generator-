<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiDelete, apiGet, apiPost, apiPut } from '@/api/client'
import type { Template } from '@/types/api'
import { useAppStore } from '@/stores/app'
import { useToast } from '@/composables/useToast'
import { fmtDate } from '@/utils/format'

const app = useAppStore()
const { toast } = useToast()

const list = ref<Template[]>([])
const filter = ref('')
const editing = ref<Template | null>(null)
const formName = ref('')
const formContent = ref('')

const filtered = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return list.value
  return list.value.filter(
    (t) => t.name.toLowerCase().includes(q) || t.content.toLowerCase().includes(q),
  )
})

async function load() {
  list.value = await apiGet<Template[]>('/api/templates')
}

onMounted(() => load().catch((e) => toast((e as Error).message)))

function startNew() {
  editing.value = null
  formName.value = ''
  formContent.value = ''
}

function edit(t: Template) {
  editing.value = t
  formName.value = t.name
  formContent.value = t.content
}

async function save() {
  const name = formName.value.trim()
  if (!name) return toast('请输入模板名称')
  try {
    if (editing.value) {
      await apiPut(`/api/templates/${encodeURIComponent(editing.value.name)}`, {
        content: formContent.value,
      })
    } else {
      await apiPost('/api/templates', { name, content: formContent.value })
    }
    toast('已保存')
    startNew()
    await load()
    await app.refreshStats()
  } catch (e) {
    toast((e as Error).message)
  }
}

async function remove(name: string) {
  if (!confirm(`删除模板「${name}」？`)) return
  await apiDelete(`/api/templates/${encodeURIComponent(name)}`)
  if (editing.value?.name === name) startNew()
  await load()
  await app.refreshStats()
  toast('已删除')
}
</script>

<template>
  <div class="page wide templates-page">
    <div class="tpl-grid">
      <section class="card">
        <div class="row head">
          <h3>模板列表</h3>
          <button type="button" class="btn sm primary" @click="startNew">新建</button>
        </div>
        <input v-model="filter" type="search" class="input" placeholder="搜索…" />
        <ul class="tpl-list">
          <li
            v-for="t in filtered"
            :key="t.name"
            :class="{ active: editing?.name === t.name }"
          >
            <button type="button" class="link-btn" @click="edit(t)">{{ t.name }}</button>
            <span class="muted">{{ fmtDate(t.updated_at) }}</span>
            <button type="button" class="del" @click="remove(t.name)">×</button>
          </li>
        </ul>
        <p v-if="!filtered.length" class="muted">暂无模板</p>
      </section>

      <section class="card">
        <h3>{{ editing ? '编辑模板' : '新建模板' }}</h3>
        <label class="field">
          <span>名称</span>
          <input v-model="formName" class="input" :disabled="!!editing" />
        </label>
        <label class="field">
          <span>内容</span>
          <textarea v-model="formContent" rows="14" class="input" />
        </label>
        <button type="button" class="btn primary" @click="save">保存</button>
      </section>
    </div>
  </div>
</template>
