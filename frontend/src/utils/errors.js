// Extrai uma mensagem legível de um erro do axios/FastAPI (inclui erros de validação 422)
export function errorMessage(error, fallback = 'Ocorreu um erro. Tente novamente.') {
  const detail = error?.response?.data?.detail
  if (!detail) {
    if (error?.response?.status === 429) return 'Muitas tentativas. Aguarde um minuto e tente novamente.'
    if (error?.code === 'ECONNABORTED') return 'O servidor demorou a responder. Tente novamente.'
    if (!error?.response && error?.message === 'Network Error') return 'Sem conexão com o servidor.'
    return fallback
  }
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const campo = Array.isArray(d.loc) ? d.loc.filter((p) => p !== 'body').join('.') : ''
        const msg = (d.msg || '').replace(/^Value error, /, '')
        return campo ? `${campo}: ${msg}` : msg
      })
      .join(' • ')
  }
  return fallback
}
