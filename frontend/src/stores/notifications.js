import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const showPanel = ref(false)

  function add(title, message, type = 'info', duration = 5000) {
    const id = Date.now() + Math.random()
    notifications.value.unshift({
      id,
      title,
      message,
      type,
      createdAt: new Date().toISOString(),
      read: false,
    })
    unreadCount.value++
  }

  function markRead(id) {
    const n = notifications.value.find(n => n.id === id)
    if (n && !n.read) {
      n.read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  function markAllRead() {
    notifications.value.forEach(n => { n.read = true })
    unreadCount.value = 0
  }

  function remove(id) {
    const idx = notifications.value.findIndex(n => n.id === id)
    if (idx === -1) return
    if (!notifications.value[idx].read) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    notifications.value.splice(idx, 1)
  }

  function togglePanel() {
    showPanel.value = !showPanel.value
  }

  async function checkExpiringPropostas() {
    try {
      const { data } = await api.get('/api/propostas?status=rascunho&limit=5')
    } catch (e) {}
  }

  return {
    notifications,
    unreadCount,
    showPanel,
    add,
    markRead,
    markAllRead,
    remove,
    togglePanel,
    checkExpiringPropostas,
  }
})
