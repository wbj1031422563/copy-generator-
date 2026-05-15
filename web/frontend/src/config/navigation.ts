/** 侧栏与路由统一的导航配置 */

export interface NavItem {
  name: string
  label: string
  icon: string
  description?: string
}

export interface NavGroup {
  id: string
  label: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    id: 'home',
    label: '工作台',
    items: [
      {
        name: 'dashboard',
        label: '概览',
        icon: 'dashboard',
        description: '数据统计与快捷入口',
      },
      {
        name: 'help',
        label: '使用指南',
        icon: 'help',
        description: '功能说明与发布流程',
      },
    ],
  },
  {
    id: 'create',
    label: '文案创作',
    items: [
      {
        name: 'chat',
        label: '对话生成',
        icon: 'chat',
        description: '单组关键词，多版本出稿',
      },
      {
        name: 'batch',
        label: '批量生成',
        icon: 'batch',
        description: '多行关键词批量铺货',
      },
      {
        name: 'keywords',
        label: '关键词库',
        icon: 'keywords',
        description: '领域词库与预设组合',
      },
    ],
  },
  {
    id: 'assets',
    label: '内容与资产',
    items: [
      {
        name: 'history',
        label: '历史记录',
        icon: 'history',
        description: '查看、对比、复用历史文案',
      },
      {
        name: 'templates',
        label: '文案模板',
        icon: 'templates',
        description: '自定义模板片段',
      },
      {
        name: 'export',
        label: '导出中心',
        icon: 'export',
        description: '批量导出 TXT / JSON',
      },
    ],
  },
  {
    id: 'tools',
    label: '工具',
    items: [
      {
        name: 'checker',
        label: '合规检测',
        icon: 'checker',
        description: '敏感词检测与净化',
      },
    ],
  },
]

export const SETTINGS_NAV: NavItem[] = [
  {
    name: 'settings-profile',
    label: '个人人设',
    icon: 'profile',
    description: '身份、亮点、联系方式',
  },
  {
    name: 'settings-services',
    label: '服务项目',
    icon: 'services',
    description: '服务类型、会议、领域词库',
  },
  {
    name: 'settings-style',
    label: '生成风格',
    icon: 'style',
    description: '版本数、语气、字数限制',
  },
  {
    name: 'settings-words',
    label: '敏感词库',
    icon: 'words',
    description: '替换规则与禁止词',
  },
  {
    name: 'settings-llm',
    label: 'LLM 配置',
    icon: 'llm',
    description: 'API Key 与模型',
  },
]

export const ALL_ROUTE_NAMES = [
  ...NAV_GROUPS.flatMap((g) => g.items.map((i) => i.name)),
  ...SETTINGS_NAV.map((i) => i.name),
]

export function isSettingsRoute(name: string | symbol | undefined | null): boolean {
  return typeof name === 'string' && name.startsWith('settings-')
}
