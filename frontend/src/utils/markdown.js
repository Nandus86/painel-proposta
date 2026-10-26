import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Renderiza Markdown escrito por usuários sempre sanitizado (evita XSS em v-html)
export function renderMarkdown(text) {
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text), { USE_PROFILES: { html: true } })
}
