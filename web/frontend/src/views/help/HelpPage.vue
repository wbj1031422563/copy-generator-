<script setup lang="ts">
import { useRouter } from 'vue-router'
import PageHeader from '@/components/layout/PageHeader.vue'
import { NAV_GROUPS, SETTINGS_NAV } from '@/config/navigation'

const router = useRouter()

function go(name: string) {
  router.push({ name })
}

const workflow = [
  { step: 1, title: '配置人设', desc: '填写博士身份、服务亮点与联系方式', route: 'settings-profile' },
  { step: 2, title: '选关键词', desc: '从词库点选或自定义研究方向', route: 'keywords' },
  { step: 3, title: '生成文案', desc: '对话生成多版本，或批量铺货', route: 'chat' },
  { step: 4, title: '合规检测', desc: '检测敏感词并净化后发布', route: 'checker' },
  { step: 5, title: '复制上架', desc: '复制标题、正文、标签到闲鱼', route: 'chat' },
]
</script>

<template>
  <div class="page wide">
    <PageHeader
      title="使用指南"
      description="闲鱼学术辅导文案工坊完整工作流与各模块说明。"
    />

    <section class="card">
      <h3>推荐工作流</h3>
      <ol class="workflow-list">
        <li v-for="w in workflow" :key="w.step" class="workflow-item">
          <span class="workflow-num">{{ w.step }}</span>
          <div>
            <strong>{{ w.title }}</strong>
            <p class="muted">{{ w.desc }}</p>
            <button type="button" class="link-btn" @click="go(w.route)">前往 →</button>
          </div>
        </li>
      </ol>
    </section>

    <div class="module-grid">
      <section
        v-for="group in NAV_GROUPS"
        :key="group.id"
        class="card module-card"
      >
        <h3>{{ group.label }}</h3>
        <ul class="module-list">
          <li v-for="item in group.items" :key="item.name">
            <button type="button" class="module-link" @click="go(item.name)">
              <span class="module-icon">{{ item.icon }}</span>
              <span>
                <strong>{{ item.label }}</strong>
                <small class="muted">{{ item.description }}</small>
              </span>
            </button>
          </li>
        </ul>
      </section>

      <section class="card module-card">
        <h3>系统设置</h3>
        <ul class="module-list">
          <li v-for="item in SETTINGS_NAV" :key="item.name">
            <button type="button" class="module-link" @click="go(item.name)">
              <span class="module-icon">{{ item.icon }}</span>
              <span>
                <strong>{{ item.label }}</strong>
                <small class="muted">{{ item.description }}</small>
              </span>
            </button>
          </li>
        </ul>
      </section>
    </div>

    <section class="card tips-card">
      <h3>闲鱼发布提示</h3>
      <ul class="tips-list">
        <li>标题控制在 30 字内，核心关键词靠前。</li>
        <li>避免「代写」「包过」等承诺性表述，系统会自动替换或标红。</li>
        <li>多版本对比后选一条发布，勿多账号发完全相同文案。</li>
        <li>可选 LLM 润色需先在「LLM 配置」中填写 API Key。</li>
      </ul>
    </section>
  </div>
</template>
