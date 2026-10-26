import api from '@/services/api'

// Baixa um arquivo autenticado da API (ex.: PDF) e dispara o download no navegador
export async function downloadFile(path, filename) {
  const response = await api.get(path, { responseType: 'blob', timeout: 120000 })
  const url = URL.createObjectURL(response.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
