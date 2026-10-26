// Utilitários dos editores com "badges" de variáveis ({{cliente}}, {{valor_total}}...)

const TAG_GLOBAL = /\{\{[a-z][a-z0-9_]*\}\}/g
// Sem a flag "g": .test() com regex global guarda lastIndex e falha em chamadas alternadas
const TAG_SINGLE = /^\{\{[a-z][a-z0-9_]*\}\}$/

const BADGE_STYLE =
  'background:rgba(59,130,246,0.12);color:#3b82f6;border:1px solid rgba(59,130,246,0.3);font-weight:600;' +
  'border-radius:4px;padding:0 6px;margin:0 1px;font-family:monospace;font-size:0.85em;cursor:default;' +
  'display:inline-block;white-space:nowrap;'

export function isVariableTag(text) {
  return TAG_SINGLE.test((text || '').trim())
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

// Texto -> HTML do editor (texto escapado; variáveis viram badges não editáveis)
export function markdownToHtml(text, badgeStyle = BADGE_STYLE) {
  if (!text) return ''
  return escapeHtml(text).replace(TAG_GLOBAL, (match) => {
    const inner = match.slice(2, -2)
    return `<span class="var-badge" contenteditable="false" data-tag="${match}" data-inner="${inner}" style="${badgeStyle}">${match}</span>`
  })
}

// HTML do editor -> texto (badges voltam a ser {{tag}} e entidades são decodificadas)
export function htmlToMarkdown(element) {
  if (!element) return ''
  let html = element.innerHTML
  html = html.replace(/<span[^>]*data-tag="([^"]*)"[^>]*>.*?<\/span>/g, (_, tag) => tag)
  html = html.replace(/<br\s*\/?>/gi, '\n')
  html = html.replace(/<div>/gi, '').replace(/<\/div>/gi, '\n')
  html = html.replace(/<\/p>/gi, '\n')
  html = html.replace(/<[^>]*>/g, '')
  const decoder = document.createElement('textarea')
  decoder.innerHTML = html
  return decoder.value.replace(/ /g, ' ').replace(/\n{3,}/g, '\n\n').trim()
}
