<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiGet } from '@/api/client'
import type { DashboardData } from '@/types/api'
import { NAV_GROUPS, SETTINGS_NAV } from '@/config/navigation'
import PageHeader from '@/components/layout/PageHeader.vue'
import UiStatCard from '@/components/ui/UiStatCard.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiEmpty from '@/components/ui/UiEmpty.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { fmtDate } from '@/utils/format'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { toast } = useToast()
const data = ref<DashboardData | null>(null)
const loading = ref(true)

const WORKFLOW = [
  {
    title: '配置人设与服务',
    desc: '在系统设置中填写身份、服务范围与 LLM Key',
    route: 'settings-profile',
  },
  {
    title: '选择关键词',
    desc: '从词库点选或对话页输入研究方向',
    route: 'keywords',
  },
  {
    title: '生成并检测',
    desc: '一次出 1–3 个版本，自动合规检测',
    route: 'chat',
  },
  {
    title: '导出发布',
    desc: '复制到闲鱼或批量导出 TXT / JSON',
    route: 'export',
  },
]

onMounted(async () => {
  try {
    data.value = await apiGet<DashboardData>('/api/dashboard')
  } catch (e) {
    toast('概览加载失败: ' + (e as Error).message)
  } finally {
    loading.value = false
  }
})

function go(name: string) {
  router.push({ name }).catch(() => {})
}

function openHistory(id: number) {
  router.push({ name: 'history', query: { id: String(id) } }).catch(() => {})
}
</script>

<template>
  <div class="page wide dashboard-page">
    <PageHeader
      title="工作台概览"
      description="学术辅导闲鱼文案 · 模板引擎 + LLM 润色 + 合规检测，一站式出稿"
    >
      <template #actions>
        <UiButton variant="primary" @click="go('chat')">
          <AppIcon name="sparkles" :size="16" />
          开始创作
        </UiButton>
        <UiButton @click="go('help')">使用指南</UiButton>
      </template>
    </PageHeader>

    <div v-if="loading" class="dashboard-loading">
      <div v-for="n in 4" :key="n" class="skeleton-stat" />
    </div>

    <template v-else-if="data">
      <div class="metrics-pro">
        <UiStatCard
          label="累计生成"
          :value="data.total_generations"
          icon="history"
          tone="accent"
        />
        <UiStatCard
          label="文案模板"
          :value="data.template_count"
          icon="templates"
        />
        <UiStatCard
          label="LLM 状态"
          :value="data.llm_configured ? '已配置' : '未配置'"
          :icon="data.llm_configured ? 'llm' : 'alert'"
          :tone="data.llm_configured ? 'ok' : 'warn'"
        />
        <UiStatCard
          label="活跃关键词"
          :value="data.top_keywords.length"
          icon="keywords"
        />
      </div>

      <div class="dash-columns">
        <UiCard title="推荐工作流" subtitle="四步完成从配置到发布">
          <ol class="workflow-list">
            <li v-for="(step, i) in WORKFLOW" :key="step.route" class="workflow-item">
              <span class="workflow-num">{{ i + 1 }}</span>
              <div class="workflow-body">
                <strong>{{ step.title }}</strong>
                <p class="muted">{{ step.desc }}</p>
                <button type="button" class="link-btn" @click="go(step.route)">
                  前往 →
                </button>
              </div>
            </li>
          </ol>
        </UiCard>

        <UiCard title="功能模块">
          <div class="module-grid compact">
            <template v-for="group in NAV_GROUPS" :key="group.id">
              <button
                v-for="item in group.items"
                :key="item.name"
                type="button"
                class="module-tile"
                @click="go(item.name)"
              >
                <span class="module-icon-wrap">
                  <AppIcon :name="item.icon" :size="22" />
                </span>
                <strong>{{ item.label }}</strong>
                <small>{{ item.description }}</small>
              </button>
            </template>
            <button
              v-for="item in SETTINGS_NAV"
              :key="item.name"
              type="button"
              class="module-tile"
              @click="go(item.name)"
            >
              <span class="module-icon-wrap">
                <AppIcon :name="item.icon" :size="22" />
              </span>
              <strong>{{ item.label }}</strong>
              <small>{{ item.description }}</small>
            </button>
          </div>
        </UiCard>
      </div>

      <div class="dash-grid">
        <UiCard title="最近生成">
          <table v-if="data.recent.length" class="table table-hover">
            <thead>
              <tr>
                <th>关键词</th>
                <th>版本</th>
                <th>时间</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in data.recent" :key="item.id">
                <td>{{ item.keywords.join(' ') }}</td>
                <td>{{ item.variant_count }}</td>
                <td class="muted">{{ fmtDate(item.created_at) }}</td>
                <td>
                  <button type="button" class="link-btn" @click="openHistory(item.id)">
                    查看
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <UiEmpty
            v-else
            title="暂无生成记录"
            description="去对话生成页输入关键词，立即出稿"
            icon="chat"
          >
            <UiButton variant="primary" @click="go('chat')">去生成</UiButton>
          </UiEmpty>
        </UiCard>

        <UiCard title="热门关键词">
          <div v-if="data.top_keywords.length" class="tags">
            <button
              v-for="k in data.top_keywords"
              :key="k.word"
              type="button"
              class="tag"
              @click="go('keywords')"
            >
              {{ k.word }} <small>{{ k.count }}</small>
            </button>
          </div>
          <UiEmpty v-else title="暂无统计数据" icon="keywords" />
        </UiCard>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-loading {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.skeleton-stat {
  height: 88px;
  border-radius: var(--radius);
  background: linear-gradient(90deg, var(--paper-2) 25%, #fff 50%, var(--paper-2) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
}
@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}
.metrics-pro {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.dash-columns {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 20px;
  margin-bottom: 20px;
}
.workflow-body strong {
  display: block;
  margin-bottom: 4px;
}
.workflow-body .link-btn {
  margin-top: 6px;
  font-size: 13px;
}
.module-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
}
.table-hover tbody tr:hover {
  background: var(--paper-2);
}
@media (max-width: 900px) {
  .dash-columns {
    grid-template-columns: 1fr;
  }
}
</style>
