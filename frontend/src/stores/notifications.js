import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

const POLL_INTERVAL_MS = 60000

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const showPanel = ref(false)
  const loading = ref(false)
  let timer = null

  async function fetch() {
    if (!localStorage.getItem('access_token')) return
    loading.value = true
    try {
      const { data } = await api.get('/api/notificacoes', { params: { limit: 20 } })
      notifications.value = data.items
      unreadCount.value = data.nao_lidas
    } catch {
      // silencioso: o sino não deve atrapalhar o uso do painel
    } finally {
      loading.value = false
    }
  }

  async function markRead(notification) {
    if (notification.lida) return
    notification.lida = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    try {
      await api.post(`/api/notificacoes/${notification.id}/lida`)
    } catch {
      // será corrigido no próximo fetch
    }
  }

  async function markAllRead() {
    notifications.value.forEach((n) => { n.lida = true })
    unreadCount.value = 0
    try {
      await api.post('/api/notificacoes/lidas')
    } catch {
      await fetch()
    }
  }

  function togglePanel() {
    showPanel.value = !showPanel.value
    if (showPanel.value) fetch()
  }

  function closePanel() {
    showPanel.value = false
  }

  function startPolling() {
    stopPolling()
    fetch()
    timer = setInterval(() => {
      if (document.visibilityState === 'visible') fetch()
    }, POLL_INTERVAL_MS)
  }

  function stopPolling() {
    if (timer) clearInterval(timer)
    timer = null
  }

  function reset() {
    stopPolling()
    notifications.value = []
    unreadCount.value = 0
    showPanel.value = false
  }

  return {
    notifications,
    unreadCount,
    showPanel,
    loading,
    fetch,
    markRead,
    markAllRead,
    togglePanel,
    closePanel,
    startPolling,
    stopPolling,
    reset,
  }
})
