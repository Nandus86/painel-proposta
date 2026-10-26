// Status de propostas e orçamentos (os valores precisam bater com os enums do backend)
const PROPOSTA = {
  rascunho: { label: 'Rascunho', severity: 'info' },
  enviada: { label: 'Enviada', severity: 'warning' },
  aceita: { label: 'Aceita', severity: 'success' },
  recusada: { label: 'Recusada', severity: 'danger' },
  expirada: { label: 'Expirada', severity: 'secondary' },
}

const ORCAMENTO = {
  rascunho: { label: 'Rascunho', severity: 'info' },
  enviado: { label: 'Enviado', severity: 'warning' },
  aprovado: { label: 'Aprovado', severity: 'success' },
  rejeitado: { label: 'Rejeitado', severity: 'danger' },
  vencido: { label: 'Vencido', severity: 'secondary' },
}

function table(tipo) {
  return tipo === 'orcamento' ? ORCAMENTO : PROPOSTA
}

export function statusOptions(tipo) {
  return Object.entries(table(tipo)).map(([value, { label }]) => ({ value, label }))
}

export function statusLabel(tipo, status) {
  return table(tipo)[status]?.label || status || ''
}

export function statusSeverity(tipo, status) {
  return table(tipo)[status]?.severity || 'info'
}
