export function fmtDate(iso: string | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso.slice(0, 16)
  }
}

export function styleLabel(style?: string): string {
  const map: Record<string, string> = {
    comprehensive: '标准版',
    concise_casual: '简洁版',
    case_led: '案例版',
    v1_standard: '标准版',
    v2_concise: '简洁版',
    v3_case_led: '案例版',
  }
  return map[style || ''] || style || '默认'
}

export function variantPlainText(v: {
  title: string
  body: string
  tags?: string[]
}): string {
  const tagLine = v.tags?.length ? `\n\n标签: ${v.tags.join(' ')}` : ''
  return `标题: ${v.title}\n\n${v.body}${tagLine}`
}

export async function copyText(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.left = '-9999px'
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
}

export async function copyVariant(v: {
  title: string
  body: string
  tags?: string[]
}): Promise<void> {
  await copyText(variantPlainText(v))
}
