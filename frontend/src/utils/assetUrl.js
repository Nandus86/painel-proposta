import api from '../services/api'

export function assetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const baseUrl = (api.defaults.baseURL || '').replace(/\/+$/, '')
  if (!baseUrl) return path
  return `${baseUrl}${path}`
}
