<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPut } from '@/api/client'
import { useToast } from '@/composables/useToast'
import { splitCsv } from '@/utils/form'

const { toast } = useToast()

const profile = ref({
  identity: '',
  role_tags: [] as string[],
  highlight: '',
  audience: [] as string[],
  contact: '',
  extra: '',
})
const roleTagsStr = ref('')
const audienceStr = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const p = await apiGet<typeof profile.value>('/api/profile')
    profile.value = p
    roleTagsStr.value = (p.role_tags || []).join('，')
    audienceStr.value = (p.audience || []).join('，')
  } catch (e) {
    toast((e as Error).message)
  } finally {
    loading.value = false
  }
})

async function save() {
  try {
    await apiPut('/api/profile', {
      ...profile.value,
      role_tags: splitCsv(roleTagsStr.value),
      audience: splitCsv(audienceStr.value),
    })
    toast('个人人设已保存')
  } catch (e) {
    toast('保存失败: ' + (e as Error).message)
  }
}
</script>

<template>
  <section class="card">
    <h3>个人人设</h3>
    <p class="muted">用于生成「本人…」开头与联系方式，体现博士个人承接而非机构。</p>
    <p v-if="loading" class="muted">加载中…</p>
    <template v-else>
      <label class="field">
        <span>身份描述</span>
        <input v-model="profile.identity" class="input" />
      </label>
      <label class="field">
        <span>角色标签（逗号分隔）</span>
        <input v-model="roleTagsStr" class="input" placeholder="个人承接，诚信第一" />
      </label>
      <label class="field">
        <span>亮点</span>
        <input v-model="profile.highlight" class="input" />
      </label>
      <label class="field">
        <span>目标受众（逗号分隔）</span>
        <input v-model="audienceStr" class="input" />
      </label>
      <label class="field">
        <span>联系方式引导</span>
        <input v-model="profile.contact" class="input" />
      </label>
      <label class="field">
        <span>补充说明 / 成果</span>
        <textarea v-model="profile.extra" class="input" rows="4" />
      </label>
      <button type="button" class="btn primary" @click="save">保存人设</button>
    </template>
  </section>
</template>
