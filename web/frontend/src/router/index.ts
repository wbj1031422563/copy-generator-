import { createRouter, createWebHistory } from 'vue-router'
import SettingsLayout from '@/layouts/SettingsLayout.vue'
import { fetchAuthStatus } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    { path: '/', redirect: '/dashboard' },

    // ── 工作台 ─────────────────────────────
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: '工作台概览', group: '工作台' },
    },
    {
      path: '/help',
      name: 'help',
      component: () => import('@/views/help/HelpPage.vue'),
      meta: { title: '使用指南', group: '工作台' },
    },

    // ── 文案创作 ───────────────────────────
    {
      path: '/generate/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: '对话生成', group: '文案创作' },
    },
    {
      path: '/generate/batch',
      name: 'batch',
      component: () => import('@/views/BatchView.vue'),
      meta: { title: '批量生成', group: '文案创作' },
    },
    {
      path: '/keywords',
      name: 'keywords',
      component: () => import('@/views/KeywordsView.vue'),
      meta: { title: '关键词库', group: '文案创作' },
    },

    // ── 内容与资产 ─────────────────────────
    {
      path: '/history',
      name: 'history',
      component: () => import('@/views/HistoryView.vue'),
      meta: { title: '历史记录', group: '内容与资产' },
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('@/views/TemplatesView.vue'),
      meta: { title: '文案模板', group: '内容与资产' },
    },
    {
      path: '/export',
      name: 'export',
      component: () => import('@/views/ExportView.vue'),
      meta: { title: '导出中心', group: '内容与资产' },
    },

    // ── 工具 ───────────────────────────────
    {
      path: '/tools/checker',
      name: 'checker',
      component: () => import('@/views/CheckerView.vue'),
      meta: { title: '合规检测', group: '工具' },
    },

    // ── 系统设置（嵌套路由）────────────────
    {
      path: '/settings',
      component: SettingsLayout,
      meta: { title: '系统设置' },
      redirect: { name: 'settings-profile' },
      children: [
        {
          path: 'profile',
          name: 'settings-profile',
          component: () => import('@/views/settings/ProfilePage.vue'),
          meta: { title: '个人人设', group: '系统设置' },
        },
        {
          path: 'services',
          name: 'settings-services',
          component: () => import('@/views/settings/ServicesPage.vue'),
          meta: { title: '服务项目', group: '系统设置' },
        },
        {
          path: 'style',
          name: 'settings-style',
          component: () => import('@/views/settings/StylePage.vue'),
          meta: { title: '生成风格', group: '系统设置' },
        },
        {
          path: 'words',
          name: 'settings-words',
          component: () => import('@/views/settings/WordsPage.vue'),
          meta: { title: '敏感词库', group: '系统设置' },
        },
        {
          path: 'llm',
          name: 'settings-llm',
          component: () => import('@/views/settings/LlmPage.vue'),
          meta: { title: 'LLM 配置', group: '系统设置' },
        },
      ],
    },

    // 兼容旧路径
    { path: '/chat', redirect: '/generate/chat' },
    { path: '/batch', redirect: '/generate/batch' },
    { path: '/checker', redirect: '/tools/checker' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  try {
    const status = await fetchAuthStatus()
    if (status.enabled && !status.authenticated) {
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      }
    }
  } catch {
    return true
  }
  return true
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || '闲鱼文案工坊'
  document.title = `${title} · 闲鱼文案工坊`
})

export default router
