import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'
import { applyTheme, resetTheme } from '../utils/theme'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)
  const setupDone = ref(null)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isGerente = computed(() => ['admin', 'gerente'].includes(user.value?.role))
  const isSuperuser = computed(() => !!user.value?.is_superuser)
  const empresaNome = computed(() => user.value?.empresa_nome || '')

  async function checkSetupStatus() {
    try {
      const { data } = await api.get('/api/setup/status')
      setupDone.value = data.setup_done
      return data.setup_done
    } catch {
      setupDone.value = false
      return false
    }
  }

  async function login(email, senha) {
    loading.value = true
    try {
      const { data } = await api.post('/api/auth/login', { email, senha })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      await fetchUser()
      return true
    } catch (error) {
      throw error.response?.data?.detail || 'Erro ao fazer login'
    } finally {
      loading.value = false
    }
  }

  async function register(nome, email, senha) {
    loading.value = true
    try {
      const { data } = await api.post('/api/auth/register', { nome, email, senha })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      await fetchUser()
      return true
    } catch (error) {
      throw error.response?.data?.detail || 'Erro ao registrar'
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      const { data } = await api.get('/api/auth/me')
      user.value = data
      if (data.empresa_cor_marca) {
        applyTheme(data.empresa_cor_marca)
      } else {
        resetTheme()
      }
    } catch {
      user.value = null
      resetTheme()
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }

  async function logout() {
    user.value = null
    resetTheme()
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function initAuth() {
    const token = localStorage.getItem('access_token')
    if (token) {
      await fetchUser()
    }
  }

  return {
    user,
    loading,
    setupDone,
    isAuthenticated,
    isAdmin,
    isGerente,
    isSuperuser,
    empresaNome,
    checkSetupStatus,
    login,
    register,
    fetchUser,
    logout,
    initAuth,
  }
})
