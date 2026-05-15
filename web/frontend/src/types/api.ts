export interface ApiResponse<T> {
  ok: boolean
  data?: T
  detail?: string
}

export interface Variant {
  title: string
  body: string
  style?: string
  version?: string
  tags?: string[]
  source?: 'llm' | 'template' | 'llm+template'
}

export interface ViolationsCheck {
  safe?: boolean
  violations?: string[]
}

export interface HistoryMeta {
  violations_check?: ViolationsCheck
  use_llm?: boolean
  llm_provider?: string
  version_count?: number
}

export interface HistoryItem {
  id: number
  keywords: string[]
  style: string
  variants: Variant[]
  meta: HistoryMeta
  variant_count: number
  created_at: string
}

export interface GenerateResult {
  keywords: string[]
  variants: Variant[]
  violations_check: ViolationsCheck
  generated_at?: string
  history_id?: number
  llm_used?: boolean
}

export interface BatchResultItem {
  keywords: string[]
  variants: Variant[]
  violations_check: ViolationsCheck
}

export interface DashboardData {
  total_generations: number
  template_count: number
  recent: HistoryItem[]
  top_keywords: { word: string; count: number }[]
  llm_configured: boolean
  llm_provider: string
}

export interface LlmConfig {
  provider: string
  base_url: string
  model: string
  api_key?: string
  has_key?: boolean
  key_hint?: string
}

export interface Template {
  id?: number
  name: string
  content: string
  updated_at: string
}

export interface KeywordDomain {
  name: string
  keywords: string[]
}

export interface CheckLayerResult {
  label: string
  hint?: string
  safe: boolean
  violations: string[]
}

export interface CheckResult {
  ok: boolean
  safe: boolean
  violations: string[]
  sanitized: string
  changed: boolean
  layers?: {
    local: CheckLayerResult
    ad_law: CheckLayerResult
  }
}

export type StyleKey = 'comprehensive' | 'concise_casual' | 'case_led'

export const STYLE_LABELS: Record<string, string> = {
  comprehensive: '标准版',
  concise_casual: '简洁版',
  case_led: '案例版',
  v1: '版本 1',
  v2: '版本 2',
  v3: '版本 3',
}
