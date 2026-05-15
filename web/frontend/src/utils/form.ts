export function linesToArr(text: string): string[] {
  return text.split('\n').map((s) => s.trim()).filter(Boolean)
}

export function arrToLines(arr: string[] | undefined): string {
  return (arr || []).join('\n')
}

export function splitCsv(text: string): string[] {
  return text.split(/[,，]/).map((s) => s.trim()).filter(Boolean)
}
